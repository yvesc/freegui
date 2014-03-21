#+
# Copyright 2010 iXsystems, Inc.
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted providing that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#####################################################################
import grp
import hashlib
import ldap
import logging
import os
import pwd
import types

from dns import resolver
from ldap.controls import SimplePagedResultsControl

from freenasUI.common.system import (
    get_freenas_var,
    get_freenas_var_by_file,
    ldap_objects,
    activedirectory_objects,
)
from freenasUI.common.freenascache import *

log = logging.getLogger('common.freenasldap')

FREENAS_LDAP_NOSSL = 0
FREENAS_LDAP_USESSL = 1
FREENAS_LDAP_USETLS = 2

FREENAS_LDAP_PORT = get_freenas_var("FREENAS_LDAP_PORT", 389)
FREENAS_LDAP_SSL_PORT = get_freenas_var("FREENAS_LDAP_SSL_PORT", 636)

FREENAS_AD_SEPARATOR = get_freenas_var("FREENAS_AD_SEPARATOR", '\\')
FREENAS_AD_CONFIG_FILE = get_freenas_var("AD_CONFIG_FILE",
    "/etc/directoryservice/ActiveDirectory/config")

FREENAS_LDAP_CACHE_EXPIRE = get_freenas_var("FREENAS_LDAP_CACHE_EXPIRE", 60)
FREENAS_LDAP_CACHE_ENABLE = get_freenas_var("FREENAS_LDAP_CACHE_ENABLE", 1)

FREENAS_LDAP_VERSION = ldap.VERSION3
FREENAS_LDAP_REFERRALS = get_freenas_var("FREENAS_LDAP_REFERRALS", 0)
FREENAS_LDAP_CACERTFILE = get_freenas_var("CERT_FILE")

FREENAS_LDAP_PAGESIZE = get_freenas_var("FREENAS_LDAP_PAGESIZE", 1024)

ldap.protocol_version = FREENAS_LDAP_VERSION
ldap.set_option(ldap.OPT_REFERRALS, FREENAS_LDAP_REFERRALS)

FLAGS_DBINIT		= 0x00010000
FLAGS_AD_ENABLED	= 0x00000001
FLAGS_LDAP_ENABLED	= 0x00000002

class FreeNAS_LDAP_Directory_Exception(Exception):
    pass
class FreeNAS_ActiveDirectory_Exception(FreeNAS_LDAP_Directory_Exception):
    pass
class FreeNAS_LDAP_Exception(FreeNAS_LDAP_Directory_Exception):
    pass


class FreeNAS_LDAP_Directory(object):
    def __init__(self, **kwargs):
        log.debug("FreeNAS_LDAP_Directory.__init__: enter")

        self.host = kwargs.get('host', None)

        self.port = None
        if kwargs.has_key('port') and kwargs['port'] is not None:
            self.port = long(kwargs['port'])

        self.binddn = kwargs.get('binddn', None)
        self.bindpw = kwargs.get('bindpw', None)
        self.basedn = kwargs.get('basedn', None)

        self.ssl = FREENAS_LDAP_NOSSL
        if kwargs.has_key('ssl') and kwargs['ssl'] is not None:
            self.ssl = self._setssl(kwargs['ssl'])
            if self.ssl is FREENAS_LDAP_USESSL and self.port is None:
                self.port = FREENAS_LDAP_SSL_PORT

        if self.port is None:
            self.port = FREENAS_LDAP_PORT

        self.scope = ldap.SCOPE_SUBTREE
        if kwargs.has_key('scope') and kwargs['scope'] is not None:
            self.scope = kwargs['scope']

        self.filter = kwargs.get('filter', None)
        self.attributes = kwargs.get('attributes', None)

        self.pagesize = 0
        if kwargs.has_key('pagesize') and kwargs['pagesize'] is not None:
            self.pagesize = kwargs['pagesize']

        self.flags = 0
        if kwargs.has_key('flags') and kwargs['flags'] is not None:
            self.flags = kwargs['flags']

        self._handle = None
        self._isopen = False
        self._cache = FreeNAS_LDAP_QueryCache()
        self._settings = []

        log.debug("FreeNAS_LDAP_Directory.__init__: "
            "host = %s, port = %ld, binddn = %s, basedn = %s, ssl = %d",
            self.host,
            self.port,
            self.binddn,
            self.basedn,
            self.ssl)
        log.debug("FreeNAS_LDAP_Directory.__init__: leave")

    def _save(self):
        _s = {}
        _s.update(self.__dict__)
        self._settings.append(_s)

    def _restore(self):
        if self._settings:
            _s = self._settings.pop()
            self.__dict__.update(_s)

    def _logex(self, ex):
        log.debug("FreeNAS_LDAP_Directory[ERROR]: An LDAP Exception occured")
        for e in ex:
            if e.has_key('info'):
                log.debug("FreeNAS_LDAP_Directory[ERROR]: info: '%s'", e['info'])
            if e.has_key('desc'):
                log.debug("FreeNAS_LDAP_Directory[ERROR]: desc: '%s'", e['desc'])

    def isOpen(self):
        return self._isopen

    def _setssl(self, ssl):
        tok = FREENAS_LDAP_NOSSL

        if type(ssl) in (types.IntType, types.LongType) or ssl.isdigit():
            ssl = int(ssl)
            if ssl not in (FREENAS_LDAP_NOSSL,
                FREENAS_LDAP_USESSL, FREENAS_LDAP_USETLS):
                tok = FREENAS_LDAP_NOSSL

        else:
            if ssl == "start_tls":
                tok = FREENAS_LDAP_USETLS
            elif ssl == "on":
                tok = FREENAS_LDAP_USESSL

        return tok

    def _geturi(self):
        if self.host is None:
            return None

        uri = None
        if self.ssl in (FREENAS_LDAP_NOSSL, FREENAS_LDAP_USETLS):
            proto = "ldap"

        elif self.ssl == FREENAS_LDAP_USESSL:
            proto = "ldaps"

        else:
            proto = "ldap"

        uri = "%s://%s:%d" % (proto, self.host, self.port)
        return uri

    def open(self):
        log.debug("FreeNAS_LDAP_Directory.open: enter")

        if self._isopen:
            return True

        if self.host:
            uri = self._geturi()
            log.debug("FreeNAS_LDAP_Directory.open: uri = %s", uri)

            self._handle = ldap.initialize(self._geturi())
            log.debug("FreeNAS_LDAP_Directory.open: initialized")

        if self._handle:
            res = None
            self._handle.protocol_version = FREENAS_LDAP_VERSION
            self._handle.set_option(ldap.OPT_REFERRALS, FREENAS_LDAP_REFERRALS)
            self._handle.set_option(ldap.OPT_NETWORK_TIMEOUT, 10.0)

            if self.ssl in (FREENAS_LDAP_USESSL, FREENAS_LDAP_USETLS):
                self._handle.set_option(ldap.OPT_X_TLS_ALLOW, 1)
                self._handle.set_option(ldap.OPT_X_TLS_CACERTFILE, FREENAS_LDAP_CACERTFILE)
                self._handle.set_option(ldap.OPT_X_TLS_NEWCTX, ldap.OPT_X_TLS_DEMAND)

            if self.ssl == FREENAS_LDAP_USETLS:
                try:
                    self._handle.start_tls_s()
                    log.debug("FreeNAS_LDAP_Directory.open: started TLS")

                except ldap.LDAPError, e:
                    self._logex(e)
                    pass

            if self.binddn and self.bindpw:
                try:
                    log.debug("FreeNAS_LDAP_Directory.open: "
                        "trying to bind to %s:%d", self.host, self.port)
                    res = self._handle.simple_bind_s(self.binddn, self.bindpw)
                    log.debug("FreeNAS_LDAP_Directory.open: binded")

                except ldap.LDAPError, e:
                    log.debug("FreeNAS_LDAP_Directory.open: "
                        "coud not bind to %s:%d", self.host, self.port)
                    self._logex(e)
                    res = None
            else:
                try:
                    log.debug("FreeNAS_LDAP_Directory.open: "
                        "(anonymous bind) trying to bind to %s:%d", self.host, self.port)
                    res = self._handle.simple_bind_s()
                    log.debug("FreeNAS_LDAP_Directory.open: binded")

                except ldap.LDAPError, e:
                    log.debug("FreeNAS_LDAP_Directory.open: "
                        "coud not bind to %s:%d", self.host, self.port)
                    self._logex(e)
                    res = None

            if res:
                self._isopen = True
                log.debug("FreeNAS_LDAP_Directory.open: connection open")

        log.debug("FreeNAS_LDAP_Directory.open: leave")
        return (self._isopen == True)

    def unbind(self):
        if self._handle:
            self._handle.unbind()
            log.debug("FreeNAS_LDAP_Directory.unbind: unbind")

    def close(self):
        if self._isopen:
            self.unbind()
            self._handle = None
            self._isopen = False
            log.debug("FreeNAS_LDAP_Directory.close: connection closed")

    def _search(self, basedn="", scope=ldap.SCOPE_SUBTREE, filter=None, attributes=None,
        attrsonly=0, serverctrls=None, clientctrls=None, timeout=-1, sizelimit=0):
        log.debug("FreeNAS_LDAP_Directory._search: enter")
        log.debug("FreeNAS_LDAP_Directory._search: basedn = '%s', filter = '%s'", basedn, filter)
        if not self._isopen:
            return None

        #
        # XXX
        # For some reason passing attributes causes paged search results to hang/fail
        # after a a certain numbe of pages. I can't figure out why. This is a workaround.
        # XXX
        #
        attributes = None

        m = hashlib.sha256()
        m.update(filter + self.host + str(self.port) + (basedn if basedn else ''))
        key = m.hexdigest()
        m = None

        if filter is not None and self._cache.has_key(key):
            log.debug("FreeNAS_LDAP_Directory._search: query in cache")
            return self._cache[key]

        result = []
        results = []
        paged = SimplePagedResultsControl(
            True,
            size=self.pagesize,
            cookie=''
        )

        paged_ctrls = {
            SimplePagedResultsControl.controlType: SimplePagedResultsControl,
        }

        if self.pagesize > 0:
            log.debug("FreeNAS_LDAP_Directory._search: pagesize = %d",
                self.pagesize)

            page = 0
            while True:
                log.debug("FreeNAS_LDAP_Directory._search: getting page %d",
                    page)
                serverctrls = [paged]

                id = self._handle.search_ext(
                   basedn,
                   scope,
                   filterstr=filter,
                   attrlist=attributes,
                   attrsonly=attrsonly,
                   serverctrls=serverctrls,
                   clientctrls=clientctrls,
                   timeout=timeout,
                   sizelimit=sizelimit
                )

                (rtype, rdata, rmsgid, serverctrls) = self._handle.result3(
                    id, resp_ctrl_classes=paged_ctrls
                )

                result.extend(rdata)

                paged.size = 0
                paged.cookie = cookie = None
                for sc in serverctrls:
                    if sc.controlType == SimplePagedResultsControl.controlType:
                        cookie = sc.cookie
                        if cookie:
                            paged.cookie = cookie
                            paged.size = self.pagesize

                        break

                if not cookie:
                    break

                page += 1
        else:
            log.debug("FreeNAS_LDAP_Directory._search: pagesize = 0")

            id = self._handle.search_ext(
                basedn,
                scope,
                filterstr=filter,
                attrlist=attributes,
                attrsonly=attrsonly,
                serverctrls=serverctrls,
                clientctrls=clientctrls,
                timeout=timeout,
                sizelimit=sizelimit
            )

            type = ldap.RES_SEARCH_ENTRY
            while type != ldap.RES_SEARCH_RESULT:
                try:
                    type, data = self._handle.result(id, 0)

                except ldap.LDAPError, e:
                    self._logex(e)
                    break

                results.append(data)

            for i in range(len(results)):
                for entry in results[i]:
                    result.append(entry)

            self._cache[key] = result

        log.debug("FreeNAS_LDAP_Directory._search: %d results", len(result))
        log.debug("FreeNAS_LDAP_Directory._search: leave")
        return result

    def search(self):
        log.debug("FreeNAS_LDAP_Directory.search: enter")
        isopen = self._isopen
        self.open()

        results = self._search(self.basedn, self.scope, self.filter, self.attributes)
        if not isopen:
            self.close()

        return results


class FreeNAS_LDAP_Base(FreeNAS_LDAP_Directory):
    def __db_init__(self, **kwargs):
        log.debug("FreeNAS_LDAP_Base.__db_init__: enter")

        ldap = ldap_objects()[0]

        host = port = None
        tmphost = ldap['ldap_hostname']
        if tmphost:
            parts = tmphost.split(':')
            host = parts[0]
            if len(parts) > 1 and parts[1]:
                port = long(parts[1])

        binddn = bindpw = None
        anonbind = ldap['ldap_anonbind']
        if not anonbind:
            binddn = ldap['ldap_rootbasedn']
            bindpw = ldap['ldap_rootbindpw']
        basedn = ldap['ldap_basedn']

        ssl = FREENAS_LDAP_NOSSL
        if ldap.has_key('ldap_ssl') and ldap['ldap_ssl']:
            ssl = ldap['ldap_ssl']

        args = {
            'binddn': binddn,
            'bindpw': bindpw,
            'basedn': basedn,
            'ssl': ssl,
            }
        if host:
            args['host'] = host
            if port:
                args['port'] = port

        if kwargs.has_key('flags'):
            args['flags'] = kwargs['flags']

        super(FreeNAS_LDAP_Base, self).__init__(**args)

        self.rootbasedn = ldap['ldap_rootbasedn']
        self.rootbindpw = ldap['ldap_rootbindpw']
        self.usersuffix = ldap['ldap_usersuffix']
        self.groupsuffix = ldap['ldap_groupsuffix']
        self.machinesuffix = ldap['ldap_machinesuffix']
        self.passwordsuffix = ldap['ldap_passwordsuffix']
        self.pwencryption = ldap['ldap_pwencryption']
        self.anonbind = ldap['ldap_anonbind']

        log.debug("FreeNAS_LDAP_Base.__db_init__: leave")

    def __no_db_init__(self, **kwargs):
        log.debug("FreeNAS_LDAP_Base.__no_db_init__: enter")

        host = None
        tmphost = kwargs.get('host', None)
        if tmphost:
            host = tmphost.split(':')[0]
            port = long(kwargs['port']) if kwargs.has_key('port') else None
            if port == None:
                tmp = tmphost.split(':')
                if len(tmp) > 1:
                    port = long(tmp[1])

        if kwargs.has_key('port') and kwargs['port'] and not port:
            port = long(kwargs['port'])

        binddn = bindpw = None
        anonbind = kwargs.get('anonbind', None)
        if not anonbind:
            binddn = kwargs.get('binddn', None)
            bindpw = kwargs.get('bindpw', None)
        basedn = kwargs.get('basedn', None)

        ssl = FREENAS_LDAP_NOSSL
        if kwargs.has_key('ssl') and kwargs['ssl']:
            ssl = kwargs['ssl']

        args = {
            'binddn': binddn,
            'bindpw': bindpw,
            'basedn': basedn,
            'ssl': ssl,
            }
        if host:
            args['host'] = host
            if port:
                args['port'] = port

        if kwargs.has_key('flags'):
            args['flags'] = kwargs['flags']

        super(FreeNAS_LDAP_Base, self).__init__(**args)

        self.rootbasedn = kwargs.get('rootbasedn', None)
        self.rootbindpw = kwargs.get('rootbindpw', None)
        self.usersuffix = kwargs.get('usersuffix', None)
        self.groupsuffix = kwargs.get('groupsuffix', None)
        self.machinesuffix = kwargs.get('machinesuffix', None)
        self.passwordsuffix = kwargs.get('passwordsuffix', None)
        self.pwencryption = kwargs.get('pwencryption', None)
        self.anonbind = kwargs.get('anonbind', None)

        log.debug("FreeNAS_LDAP_Base.__no_db_init__: leave")

    def __init__(self, **kwargs):
        log.debug("FreeNAS_LDAP_Base.__init__: enter")

        __initfunc__ = self.__no_db_init__
        if kwargs.has_key('flags') and (kwargs['flags'] & FLAGS_DBINIT):
            __initfunc__ = self.__db_init__

        __initfunc__(**kwargs)
        self.ucount = 0
        self.gcount = 0

        log.debug("FreeNAS_LDAP_Base.__init__: leave")

    def get_user(self, user):
        log.debug("FreeNAS_LDAP_Base.get_user: enter")
        log.debug("FreeNAS_LDAP_Base.get_user: user = %s", user)

        if user is None:
            raise AssertionError('user is None')

        isopen = self._isopen
        self.open()

        ldap_user = None
        scope = ldap.SCOPE_SUBTREE

        if type(user) in (types.IntType, types.LongType):
            filter = '(&(|(objectclass=person)(objectclass=account))(uidnumber=%d))' % user

        elif user.isdigit():

            filter = '(&(|(objectclass=person)(objectclass=account))(uidnumber=%s))' % user
        else:
            filter = '(&(|(objectclass=person)(objectclass=account))(|(uid=%s)(cn=%s)))' % (user, user)

        basedn = None
        if self.usersuffix and self.basedn:
            basedn = "%s,%s" % (self.usersuffix, self.basedn)
        elif self.basedn:
            basedn = "%s" % self.basedn

        args = {'scope': scope, 'filter': filter}
        if basedn:
            args['basedn'] = basedn
        if self.attributes:
            args['attributes'] = self.attributes

        results = self._search(**args)
        if results:
            for r in results:
                if r[0]:
                    ldap_user = r
                    break

        if not isopen:
            self.close()

        log.debug("FreeNAS_LDAP_Base.get_user: leave")
        return ldap_user

    def get_users(self):
        log.debug("FreeNAS_LDAP_Base.get_users: enter")
        isopen = self._isopen
        self.open()

        users = []
        scope = ldap.SCOPE_SUBTREE
        filter = '(&(|(objectclass=person)(objectclass=account))(uid=*))'

        if self.usersuffix:
            basedn = "%s,%s" % (self.usersuffix, self.basedn)
        else:
            basedn = "%s" % self.basedn
	
        results = self._search(basedn, scope, filter, self.attributes)
        if results:
            for r in results:
                if r[0]:
                    users.append(r)

        if not isopen:
            self.close()

        log.debug("FreeNAS_LDAP_Base.get_users: leave")
        return users

    def get_group(self, group):
        log.debug("FreeNAS_LDAP_Base.get_group: enter")
        log.debug("FreeNAS_LDAP_Base.get_group: group = %s", group)

        if group is None:
            raise AssertionError('group is None')

        isopen = self._isopen
        self.open()

        ldap_group = None
        scope = ldap.SCOPE_SUBTREE

        if type(group) in (types.IntType, types.LongType):
            filter = '(&(objectclass=posixgroup)(gidnumber=%d))' % group
        elif group.isdigit():
            filter = '(&(objectclass=posixgroup)(gidnumber=%s))' % group
        else:
            filter = '(&(objectclass=posixgroup)(cn=%s))' % group

        if self.groupsuffix:
            basedn = "%s,%s" % (self.groupsuffix, self.basedn)
        else:
            basedn = "%s" % self.basedn

        results = self._search(basedn, scope, filter, self.attributes)
        if results:
            for r in results:
                if r[0]:
                    ldap_group = r
                    break

        if not isopen:
            self.close()

        log.debug("FreeNAS_LDAP_Base.get_group: leave")
        return ldap_group

    def get_groups(self):
        log.debug("FreeNAS_LDAP_Base.get_groups: enter")
        isopen = self._isopen
        self.open()

        groups = []
        scope = ldap.SCOPE_SUBTREE
        filter = '(&(objectclass=posixgroup)(gidnumber=*))'

        if self.groupsuffix:
            basedn = "%s,%s" % (self.groupsuffix, self.basedn)
        else:
            basedn = "%s" % self.basedn
	
        results = self._search(basedn, scope, filter, self.attributes)
        if results:
            for r in results:
                if r[0]:
                    groups.append(r)

        if not isopen:
            self.close()

        log.debug("FreeNAS_LDAP_Base.get_groups: leave")
        return groups


class FreeNAS_LDAP(FreeNAS_LDAP_Base):
    def __init__(self, **kwargs):
        log.debug("FreeNAS_LDAP.__init__: enter")

        super(FreeNAS_LDAP, self).__init__(**kwargs)

        log.debug("FreeNAS_LDAP.__init__: leave")


class FreeNAS_ActiveDirectory_Base(FreeNAS_LDAP_Directory):

    @staticmethod
    def get_domain_controllers(domain):
        log.debug("FreeNAS_ActiveDirectory_Base.get_domain_controllers: enter")
        dcs = []

        if not domain:
            return dcs

        host = "_ldap._tcp.%s" % domain

        try:
            log.debug("FreeNAS_ActiveDirectory_Base.get_domain_controllers: "
                "looking up SRV records for %s", host)
            answers = resolver.query(host, 'SRV')
            dcs = sorted(answers, key=lambda a: (int(a.priority), int(a.weight)))

        except:
            log.debug("FreeNAS_ActiveDirectory_Base.get_domain_controllers: "
                "no SRV records for %s found, fail!", host)
            dcs = []

        log.debug("FreeNAS_ActiveDirectory_Base.get_domain_controllers: leave")
        return dcs

    @staticmethod
    def get_global_catalogs(domain):
        log.debug("FreeNAS_ActiveDirectory_Base.get_global_catalogs: enter")
        gcs = []

        if not domain:
            return gcs

        host = "_gc._tcp.%s" % domain

        try:
            log.debug("FreeNAS_ActiveDirectory_Base.get_global_catalogs: "
                "looking up SRV records for %s", host)
            answers = resolver.query(host, 'SRV')
            gcs = sorted(answers, key=lambda a: (int(a.priority), int(a.weight)))

        except:
            log.debug("FreeNAS_ActiveDirectory_Base.get_global_catalogs: "
                "no SRV records for %s found, fail!", host)
            gcs = []

        log.debug("FreeNAS_ActiveDirectory_Base.get_global_catalogs: leave")
        return gcs

    @staticmethod
    def dc_connect(domain, binddn, bindpw):
        log.debug("FreeNAS_ActiveDirectory_Base.dc_connect: enter")
        log.debug("FreeNAS_ActiveDirectory_Base.dc_connect: domain = %s",
            domain)

        ret = False
        args = {'binddn': binddn, 'bindpw': bindpw}

        host = port = None
        dcs = FreeNAS_ActiveDirectory_Base.get_domain_controllers(domain)
        for dc in dcs:
            log.debug("FreeNAS_ActiveDirectory_Base.dc_connect: "
                "trying [%s]...", dc)

            args['domain'] = domain
            args['host'] = dc.target.to_text(True)
            args['port'] = long(dc.port)

            ad = FreeNAS_ActiveDirectory_Base(**args)

            ret = ad.open()
            if ret == True:
                host = ad.host
                port = ad.port
                ret = (host, port)
                break

            ad.close()

        if not ret:
            ret = (None, None)
            log.debug("FreeNAS_ActiveDirectory_Base.dc_connect: "
                "unable to connect to a domain controller")

        log.debug("FreeNAS_ActiveDirectory_Base.dc_connect: leave")
        return ret

    @staticmethod
    def adset(val, default=None):
        ret = default
        if val:
            ret = val
        return ret

    def __new__(cls, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Base.__new__: enter")

        obj = None
        if kwargs:
            obj = super(FreeNAS_ActiveDirectory_Base, cls).__new__(cls, **kwargs)

        log.debug("FreeNAS_ActiveDirectory_Base.__new__: leave")
        return obj

    def __set_defaults(self):
        log.debug("FreeNAS_ActiveDirectory_Base.__set_defaults: enter")

        self.adminname = None
        self.basedn = None
        self.binddn = None
        self.bindpw = None
        self.domain = None
        self.dcname = None
        self.dchost = None
        self.dcport = None
        self.gcname = None
        self.gchost = None
        self.gcport = None
        self.netbiosname = None
        self.unix = None
        self.default = None
        self.trusted = None

        log.debug("FreeNAS_ActiveDirectory_Base.__set_defaults: leave")

    def __get_config(self):
        log.debug("FreeNAS_ActiveDirectory_Base.__get_config: enter")

        res = False
        self.config = {
            'adminname': None, 
            'domainname': None,
            'basedn': None,
            'binddn': None,
            'dcname': None,
            'dchost': None,
            'dcport': None,
            'gcname': None,
            'gchost': None,
            'gcport': None
        }

        if os.access(FREENAS_AD_CONFIG_FILE, os.F_OK):
            for var in self.config:
                self.config[var] = get_freenas_var_by_file(FREENAS_AD_CONFIG_FILE, "ad_%s" % var)
                if self.config[var]:
                    res = True
        else:
            log.debug("FreeNAS_ActiveDirectory_Base.__get_config: leave")
            return res

        self.adminname = self.adset(self.config['adminname'])
        self.basedn = self.adset(self.config['basedn'])
        #self.binddn = self.adset(self.config['binddn'])
        #self.bindpw = self.adset(self.config['bindpw'])
        self.domain = self.adset(self.config['domainname'])

        self.dchost = None
        self.dcport = None
        self.dcname = self.adset(self.config['dcname'])
        if self.dcname:
            parts = self.dcname.split(':')
            self.dchost = parts[0]
            if len(parts) > 1:
                self.dcport = parts[1]

        self.dchost = self.adset(self.dchost, self.config['dchost'])
        self.dcport = self.adset(self.dcport, self.config['dcport'])
        self.dcport = self.adset(self.dcport, 389)

        self.gchost = None
        self.gcport = None
        self.gcname = self.adset(self.config['gcname'])
        if self.gcname:
            parts = self.gcname.split(':')
            self.gchost = parts[0]
            if len(parts) > 1:
                self.gcport = parts[1]

        self.gchost = self.adset(self.gchost, self.config['gchost'])
        self.gcport = self.adset(self.gcport, self.config['gcport'])
        self.gcport = self.adset(self.gcport, 3268)

        log.debug("FreeNAS_ActiveDirectory_Base.__get_config: leave")
        return res


    def __db_init__(self, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Base.__db_init__: enter")

        ad = activedirectory_objects()[0]

        self.domain = self.adset(self.domain, ad['ad_domainname'])
        self.netbiosname = self.adset(self.netbiosname, ad['ad_workgroup'])

        self.binddn = self.adset(self.binddn, ad['ad_bindname'] + '@' + self.domain.upper())
        self.bindpw = self.adset(self.bindpw, ad['ad_bindpw'])

        self.trusted = True if self.trusted else False
        self.trusted = self.adset(self.trusted, True if long(ad['ad_allow_trusted_doms']) != 0 else False)

        self.default = True if self.default else False
        self.default = self.adset(self.default, True if long(ad['ad_use_default_domain']) != 0 else False)

        self.unix = True if self.unix else False 
        self.unix = self.adset(self.unix, True if long(ad['ad_unix_extensions']) != 0 else False)

        host = port = None
        args = {'binddn': self.binddn, 'bindpw': self.bindpw}

        if not self.dchost:
            (host, port) = self.dc_connect(self.domain, self.binddn, self.bindpw)
        else:
            host = self.dchost
            port = self.dcport

        args['host'] = host
        args['port'] = port

        if kwargs.has_key('flags'):
            args['flags'] = kwargs['flags']

        super(FreeNAS_ActiveDirectory_Base, self).__init__(**args)

        self.basedn = self.adset(self.basedn, self.get_baseDN())
        self.netbiosname = self.adset(self.netbiosname, self.get_netbios_name())

        log.debug("FreeNAS_ActiveDirectory_Base.__db_init__: leave")

    def __no_db_init__(self, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Base.__no_db_init__: enter")

        host = port = None
        self.domain = self.adset(self.domain, kwargs.get('domain', None))
        self.netbiosname = self.adset(self.netbiosname, kwargs.get('netbiosname', None))
        self.trusted = False
        self.default = False
        self.unix = False

        self.dchost = self.adset(self.dchost, kwargs.get('host', None))
        self.dcport = self.adset(self.dcport, kwargs.get('port', None))

        tmphost = kwargs.get('host', None)
        if tmphost:
            host = tmphost.split(':')[0]
            port = long(kwargs['port']) if kwargs.has_key('port') else None
            if port == None:
                tmp = tmphost.split(':')
                if len(tmp) > 1:
                    port = long(tmp[1])

        if kwargs.has_key('port') and kwargs['port'] and not port:
            port = long(kwargs['port'])

        self.binddn = self.adset(self.binddn, kwargs.get('binddn', None))
        self.bindpw = self.adset(self.bindpw, kwargs.get('bindpw', None))

        args = {'binddn': self.binddn, 'bindpw': self.bindpw}
        if host:
            args['host'] = host
            if port:
                args['port'] = port

        if not host and not self.domain:
            log.debug("FreeNAS_ActiveDirectory_Base.__no_db_init__: "
                "neither host nor domain specified, nothing will work, #fail.")

        (host, port) = (None, None) 
        if self.dcname:
            parts = self.dcname.split(':')
            self.dchost = parts[0]
            if len(parts) > 1:
                self.dcport = parts[1]

        if not self.dchost:
            (host, port) = self.dc_connect(self.domain, self.binddn, self.bindpw)
        else:
            host = self.dchost
            port = self.dcport

        args['host'] = host
        args['port'] = port

        if kwargs.has_key('flags'):
            args['flags'] = kwargs['flags']

        super(FreeNAS_ActiveDirectory_Base, self).__init__(**args)

        self.basedn = self.adset(self.basedn, self.get_baseDN())
        self.netbiosname = self.adset(self.netbiosname, self.get_netbios_name())

        log.debug("FreeNAS_ActiveDirectory_Base.__no_db_init__: leave")

    def __init__(self, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Base.__init__: enter")

        self.__set_defaults()
        self.__get_config()

        __initfunc__ = self.__no_db_init__
        if kwargs.has_key('flags') and (kwargs['flags'] & FLAGS_DBINIT):
            __initfunc__ = self.__db_init__

        __initfunc__(**kwargs)
        self.ucount = 0
        self.gcount = 0

        log.debug("FreeNAS_ActiveDirectory_Base.__init__: leave")

    def get_rootDSE(self):
        log.debug("FreeNAS_ActiveDirectory_Base.get_rootDSE: enter")
        isopen = self._isopen
        self.open()

        results = self._search('', ldap.SCOPE_BASE, "(objectclass=*)")
        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_rootDSE: leave")
        return results

    def get_rootDN(self):
        log.debug("FreeNAS_ActiveDirectory_Base.get_rootDN: enter")
        isopen = self._isopen
        self.open()

        results = self.get_rootDSE()
        try:
            results = results[0][1]['rootDomainNamingContext'][0]

        except:
            results = None

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_rootDN: leave")
        return results

    def get_baseDN(self):
        log.debug("FreeNAS_ActiveDirectory_Base.get_baseDN: enter")
        isopen = self._isopen
        self.open()

        results = self.get_rootDSE()
        try:
            results = results[0][1]['defaultNamingContext'][0]

        except:
            results = None

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_baseDN: leave")
        return results

    def get_config(self):
        log.debug("FreeNAS_ActiveDirectory_Base.get_config: enter")
        isopen = self._isopen
        self.open()

        results = self.get_rootDSE()
        try:
            results = results[0][1]['configurationNamingContext'][0]

        except:
            results = None

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_config: leave")
        return results

    def get_netbios_name(self):
        log.debug("FreeNAS_ActiveDirectory_Base.get_netbios_name: enter")
        isopen = self._isopen
        self.open()

        basedn = self.get_baseDN()
        config = self.get_config()
        filter = "(&(objectcategory=crossref)(nCName=%s))" % basedn

        netbios_name = None
        results = self._search(config, ldap.SCOPE_SUBTREE, filter)
        try:
            netbios_name = results[0][1]['nETBIOSName'][0]

        except:
            netbios_name = None

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_netbios_name: leave")
        return netbios_name

    def get_partitions(self, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Base.get_partition: enter")
        isopen = self._isopen
        self.open()

        config = self.get_config()
        basedn = "CN=Partitions,%s" % config

        filter = None
        keys = ['netbiosname', 'name', 'cn', 'dn', 'distinguishedname', 'ncname']
        for k in keys:
            if kwargs.has_key(k):
                filter = "(%s=%s)" % (k, kwargs[k])
                break

        if filter is None:
            filter = "(cn=*)"

        partitions = []
        results = self._search(basedn, ldap.SCOPE_SUBTREE, filter)
        if results:
            for r in results:
                if r[0]:
                    partitions.append(r)

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_partition: leave")
        return partitions

    def get_root_domain(self, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Base.get_root_domain: enter")
        isopen = self._isopen
        self.open()

        rootDSE = self.get_rootDSE()
        rdnc = rootDSE[0][1]['rootDomainNamingContext'][0]

        domain = None
        results = self.get_partitions(ncname=rdnc)
        try:
            domain = results[0][1]['dnsRoot'][0]

        except:
            domain = None

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_root_domain: leave")
        return domain

    def get_domain(self, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Base.get_domain: enter")
        isopen = self._isopen
        self.open()

        domain = None
        results = self.get_partitions(**kwargs)
        try:
            domain = results[0][1]['dnsRoot'][0]

        except:
            domain = None

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_domain: leave")
        return domain

    def get_domains(self, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Base.get_domains: enter")
        isopen = self._isopen
        self.open()

        gc = None
        gc_args = {'binddn': self.binddn, 'bindpw': self.bindpw}

        root = self.get_root_domain()
        if not self.gchost:
            gcs = self.get_global_catalogs(root)

            for g in gcs:
                log.debug("FreeNAS_ActiveDirectory_Base.get_domains: trying [%s]...", g)

                gc_args['host'] = g.target.to_text(True)
                gc_args['port'] = long(g.port)

                gc = FreeNAS_LDAP_Directory(**gc_args)
                gc.open()

                if gc._isopen:
                    break

                gc.close()
                gc = None

        else:
            gc_args['host'] = self.gchost
            gc_args['port'] = long(self.gcport)

            gc = FreeNAS_LDAP_Directory(**gc_args)
            gc.open()


        domains = []
        if gc and gc._isopen:
            results = gc._search("", ldap.SCOPE_SUBTREE, '(objectclass=domain)', ['dn'])
            if not results:
                log.debug("FreeNAS_ActiveDirectory_Base.get_domains: no domain objects found")
                results = []

            for r in results:
                domains.append(r[0])

            gc.close()

        else:
            log.debug("FreeNAS_ActiveDirectory_Base.get_domains: "
                "unable to connect to a global catalog server")

        rootDSE = self.get_rootDSE()
        basedn = rootDSE[0][1]['configurationNamingContext'][0]
        #config = rootDSE[0][1]['defaultNamingContext'][0]

        if not self.trusted and self.netbiosname:
            kwargs['netbiosname'] = self.netbiosname

        result = []
        haskey = False
        for d in domains:
            filter = None
            if len(kwargs) > 0:
                haskey = True
                keys = ['netbiosname', 'name', 'cn', 'dn', 'distinguishedname', 'ncname']
                for k in keys:
                    if kwargs.has_key(k):
                        filter = "(&(objectcategory=crossref)(%s=%s))" % (k, kwargs[k])
                        break

            if filter is None:
                filter = "(&(objectcategory=crossref)(nCName=%s))" % d

            results = self._search(basedn, ldap.SCOPE_SUBTREE, filter)
            if results and results[0][0]:
                r = {}
                for k in results[0][1].keys():
                    r[k] = results[0][1][k][0]
                result.append(r)

            if haskey:
                break

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_domains: leave")
        return result

    def get_userDN(self, user):
        log.debug("FreeNAS_ActiveDirectory_Base.get_userDN: enter")
        log.debug("FreeNAS_ActiveDirectory_Base.get_userDN: user = %s", user)

        if user is None:
            raise AssertionError('user is None')

        if not self.binddn or not self.bindpw or not self.basedn:
            return None

        isopen = self._isopen
        self.open()

        scope = ldap.SCOPE_SUBTREE
        filter = '(&(|(objectclass=user)(objectclass=person))(sAMAccountName=%s))' % user
        attributes = ['distinguishedName']
        results = self._search(self.basedn, scope, filter, attributes)
        try:
            results = results[0][1][attributes[0]][0]

        except:
            results = None

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_userDN: leave")
        return results

    def get_user(self, user):
        log.debug("FreeNAS_ActiveDirectory_Base.get_user: enter")
        log.debug("FreeNAS_ActiveDirectory_Base.get_user: user = %s", user)

        if user is None:
            raise AssertionError('user is None')

        isopen = self._isopen
        self.open()

        ad_user = None
        scope = ldap.SCOPE_SUBTREE
        filter = '(&(|(objectclass=user)(objectclass=person))(sAMAccountName=%s))' % user
        results = self._search(self.basedn, scope, filter, self.attributes)
        if results:
            for r in results:
                if r[0]:
                    ad_user = r
                    break

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_user: leave")
        return ad_user

    def get_users(self):
        log.debug("FreeNAS_ActiveDirectory_Base.get_users: enter")
        isopen = self._isopen
        self.open()

        users = []
        scope = ldap.SCOPE_SUBTREE
        filter = '(&(|(objectclass=user)(objectclass=person))(sAMAccountName=*))'
        if self.attributes and 'sAMAccountType' not in self.attributes:
            self.attributes.append('sAMAccountType')

        results = self._search(self.basedn, scope, filter, self.attributes)
        if results:
            for r in results:
                if r[0] and r[1] and r[1].has_key('sAMAccountType'):
                    type = int(r[1]['sAMAccountType'][0])
                    if not (type & 0x1):
                        users.append(r)

        if not isopen:
            self.close()

        self.ucount = len(users)
        log.debug("FreeNAS_ActiveDirectory_Base.get_users: leave")
        return users

    def get_groupDN(self, group):
        log.debug("FreeNAS_ActiveDirectory_Base.get_groupDN: enter")
        log.debug("FreeNAS_ActiveDirectory_Base.get_groupDN: group = %s", group)

        if group is None:
            raise AssertionError('group is None')

        if not self.binddn or not self.bindpw or not self.basedn:
            return None

        isopen = self._isopen
        self.open()

        scope = ldap.SCOPE_SUBTREE
        filter = '(&(objectclass=group)(sAMAccountName=%s))' % group
        attributes = ['distinguishedName']
        results = self._search(self.basedn, scope, filter, attributes)
        try:
            results = results[0][1][attributes[0]][0]

        except:
            results = None

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_groupDN: leave")
        return results

    def get_group(self, group):
        log.debug("FreeNAS_ActiveDirectory_Base.get_group: enter")
        log.debug("FreeNAS_ActiveDirectory_Base.get_group: group = %s", group)

        if group is None:
            raise AssertionError('group is None')

        isopen = self._isopen
        self.open()

        ad_group = None
        scope = ldap.SCOPE_SUBTREE
        filter = '(&(objectclass=group)(sAMAccountName=%s))' % group
        results = self._search(self.basedn, scope, filter, self.attributes)
        if results:
            for r in results:
                if r[0]:
                    ad_group = r
                    break

        if not isopen:
            self.close()

        log.debug("FreeNAS_ActiveDirectory_Base.get_group: leave")
        return ad_group

    def get_groups(self):
        log.debug("FreeNAS_ActiveDirectory_Base.get_groups: enter")
        isopen = self._isopen
        self.open()

        groups = []
        scope = ldap.SCOPE_SUBTREE
        filter = '(&(objectclass=group)(sAMAccountName=*))'
        if self.attributes and 'groupType' not in self.attributes:
            self.attributes.append('groupType')

        results = self._search(self.basedn, scope, filter, self.attributes)
        if results:
            for r in results:
                if r[0]:
                    type = int(r[1]['groupType'][0])
                    if not (type & 0x1):
                        groups.append(r)

        if not isopen:
            self.close()

        self.ucount = len(groups)
        log.debug("FreeNAS_ActiveDirectory_Base.get_groups: leave")
        return groups

    def get_user_count(self):
        count = 0

        if self.ucount > 0:
            count = self.ucount

        else:
            pagesize = self.pagesize
            self.pagesize = 32768

            self.get_users()

            self.pagesize = pagesize
            count = self.ucount

        return count

    def get_group_count(self):
        count = 0

        if self.gcount > 0:
            count = self.gcount

        else:
            pagesize = self.pagesize
            self.pagesize = 32768

            self.get_groups()

            self.pagesize = pagesize
            count = self.gcount

        return count


class FreeNAS_ActiveDirectory(FreeNAS_ActiveDirectory_Base):
    def __init__(self, **kwargs):
        log.debug("FreeNAS_ActiveDirectory.__init__: enter")

        super(FreeNAS_ActiveDirectory, self).__init__(**kwargs)

        log.debug("FreeNAS_ActiveDirectory.__init__: leave")


class FreeNAS_LDAP_Users(FreeNAS_LDAP):
    def __init__(self, **kwargs):
        log.debug("FreeNAS_LDAP_Users.__init__: enter")

        super(FreeNAS_LDAP_Users, self).__init__(**kwargs)

        if (self.flags & FLAGS_CACHE_READ_USER) or \
            (self.flags & FLAGS_CACHE_WRITE_USER):
            self.__ucache = FreeNAS_UserCache()
            self.__ducache = FreeNAS_Directory_UserCache()

        self.__users = []
        self.__get_users()

        log.debug("FreeNAS_LDAP_Users.__init__: leave")

    def __loaded(self, index, write=False):
        ret = False

        ucachedir = self.__ucache.cachedir
        ducachedir = self.__ducache.cachedir

        paths = {}
        paths['u'] = os.path.join(ucachedir, ".ul")
        paths['du'] = os.path.join(ducachedir, ".dul")

        file = None
        try:
            file = paths[index]

        except:
            pass

        if file and write:
            try:
                with open(file, 'w+') as f:
                    f.close()
                ret = True

            except:
                ret = False

        elif file:
            if os.access(file, os.F_OK):
                ret = True

        return ret

    def __len__(self):
        return len(self.__users)

    def __iter__(self):
        for user in self.__users:
            yield user

    def __get_users(self):
        log.debug("FreeNAS_LDAP_Users.__get_users: enter")

        if (self.flags & FLAGS_CACHE_READ_USER) and self.__loaded('u'):
            log.debug("FreeNAS_LDAP_Users.__get_users: users in cache")
            log.debug("FreeNAS_LDAP_Users.__get_users: leave")
            self.__users = self.__ucache
            return

        self.attributes = ['uid']
        self.pagesize = FREENAS_LDAP_PAGESIZE

        if (self.flags & FLAGS_CACHE_READ_USER) and self.__loaded('du'):
            log.debug("FreeNAS_LDAP_Users.__get_users: LDAP users in cache")
            ldap_users = self.__ducache

        else:
            log.debug("FreeNAS_LDAP_Users.__get_users: LDAP users not in cache")
            ldap_users = self.get_users()

        for u in ldap_users:
            CN = str(u[0])
            if self.flags & FLAGS_CACHE_WRITE_USER:
                self.__ducache[CN] = u

            u = u[1]
            uid = str(u['uid'][0])
            try:
                pw = pwd.getpwnam(uid)

            except:
                continue

            self.__users.append(pw)
            if self.flags & FLAGS_CACHE_WRITE_USER:
                self.__ucache[uid] = pw

            pw = None

        if self.flags & FLAGS_CACHE_WRITE_USER:
            self.__loaded('u', True)
            self.__loaded('du', True)

        log.debug("FreeNAS_LDAP_Users.__get_users: leave")


class FreeNAS_ActiveDirectory_Users(FreeNAS_ActiveDirectory):
    def __init__(self, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Users.__init__: enter")

        super(FreeNAS_ActiveDirectory_Users, self).__init__(**kwargs)

        self.__users = {}
        self.__ucache = {}
        self.__ducache = {}

        if kwargs.has_key('netbiosname') and kwargs['netbiosname']:
            self.__domains = self.get_domains(netbiosname=kwargs['netbiosname'])
        else:
            self.__domains = self.get_domains()

        if (self.flags & FLAGS_CACHE_READ_USER) or \
            (self.flags & FLAGS_CACHE_WRITE_USER):
            for d in self.__domains:
                n = d['nETBIOSName']
                self.__ucache[n] = FreeNAS_UserCache(dir=n)
                self.__ducache[n] = FreeNAS_Directory_UserCache(dir=n)

        self.__get_users()

        log.debug("FreeNAS_ActiveDirectory_Users.__init__: leave")

    def __loaded(self, index, netbiosname, write=False):
        ret = False

        paths = {}
        ucachedir = self.__ucache[netbiosname].cachedir
        paths['u'] = os.path.join(ucachedir, ".ul")

        ducachedir = self.__ducache[netbiosname].cachedir 
        paths['du'] = os.path.join(ducachedir, ".dul")
   
        file = None
        try:
            file = paths[index]

        except:
            file = None

        if file and write:
            try:
                with open(file, 'w+') as f:
                    f.close()
                ret = True 

            except:
                ret = False

        elif file:
            if os.access(file, os.F_OK):
                ret = True

        return ret

    def __len__(self):
        length = 0
        for d in self.__domains:
            length += len(self.__users[d['nETBIOSName']])
        return length

    def __iter__(self):
        for d in self.__domains:
            for user in self.__users[d['nETBIOSName']]:
                yield user

    def __get_users(self):
        log.debug("FreeNAS_ActiveDirectory_Users.__get_users: enter")

        if (self.flags & FLAGS_CACHE_READ_USER):
            dcount = len(self.__domains)
            count = 0

            for d in self.__domains:
                n = d['nETBIOSName']
                if self.__loaded('u', n):
                    self.__users[n] = self.__ucache[n]
                    count += 1

            if count == dcount:
                log.debug("FreeNAS_ActiveDirectory_Users.__get_users: users in cache")
                log.debug("FreeNAS_ActiveDirectory_Users.__get_users: leave")
                return

        self._save()
        for d in self.__domains:
            n = d['nETBIOSName']
            self.__users[n] = []

            dcs = self.get_domain_controllers(d['dnsRoot'])
            (self.host, self.port) = self.dc_connect(d['dnsRoot'], self.binddn, self.bindpw)

            self.basedn = d['nCName']
            self.attributes = ['sAMAccountName']
            self.pagesize = FREENAS_LDAP_PAGESIZE

            self.close()
            self.open()

            if (self.flags & FLAGS_CACHE_READ_USER) and self.__loaded('du', n):
                log.debug("FreeNAS_ActiveDirectory_Users.__get_users: "
                    "AD [%s] users in cache" % n)
                ad_users = self.__ducache[n]

            else:
                log.debug("FreeNAS_ActiveDirectory_Users.__get_users: "
                    "AD [%s] users not in cache" % n)
                ad_users = self.get_users()

            for u in ad_users:
                CN = str(u[0])

                if self.flags & FLAGS_CACHE_WRITE_USER:
                    self.__ducache[n][CN] = u

                u = u[1]
                if self.default or self.unix:
                    sAMAccountName = u['sAMAccountName'][0]
                else:
                    sAMAccountName = str("%s%s%s" % (n, FREENAS_AD_SEPARATOR, u['sAMAccountName'][0]))

                try:
                    pw = pwd.getpwnam(sAMAccountName)

                except Exception, e:
                    log.debug("Error on getpwnam: %s", e)
                    continue

                self.__users[n].append(pw)
                if self.flags & FLAGS_CACHE_WRITE_USER:
                    self.__ucache[n][sAMAccountName] = pw

                pw = None

            if self.flags & FLAGS_CACHE_WRITE_USER:
                self.__loaded('u', n, True)
                self.__loaded('du', n, True)

        self._restore()
        log.debug("FreeNAS_ActiveDirectory_Users.__get_users: leave")


class FreeNAS_Directory_Users(object):
    def __new__(cls, **kwargs):
        log.debug("FreeNAS_Directory_Users.__new__: enter")

        dflags = 0
        if kwargs.has_key('dflags'):
            dflags = kwargs['dflags']

        obj = None
        if dflags & FLAGS_LDAP_ENABLED:
            obj = FreeNAS_LDAP_Users(**kwargs)

        elif dflags & FLAGS_AD_ENABLED:
            obj = FreeNAS_ActiveDirectory_Users(**kwargs)

        log.debug("FreeNAS_Directory_Users.__new__: leave")
        return obj


class FreeNAS_LDAP_Groups(FreeNAS_LDAP):
    def __init__(self, **kwargs):
        log.debug("FreeNAS_LDAP_Groups.__init__: enter")

        super(FreeNAS_LDAP_Groups, self).__init__(**kwargs)

        if (self.flags & FLAGS_CACHE_READ_GROUP) or \
            (self.flags & FLAGS_CACHE_WRITE_GROUP):
            self.__gcache = FreeNAS_GroupCache()
            self.__dgcache = FreeNAS_Directory_GroupCache()

        self.__groups = []
        self.__get_groups()

        log.debug("FreeNAS_LDAP_Groups.__init__: leave")

    def __loaded(self, index, write=False):
        ret = False

        gcachedir = self.__gcache.cachedir
        dgcachedir = self.__dgcache.cachedir

        paths = {}
        paths['g'] = os.path.join(gcachedir, ".gl")
        paths['dg'] = os.path.join(dgcachedir, ".dgl")

        file = None
        try:
            file = paths[index]

        except:
            pass

        if file and write:
            try:
                with open(file, 'w+') as f:
                    f.close()
                ret = True

            except:
                ret = False

        elif file:
            if os.access(file, os.F_OK):
                ret = True

        return ret

    def __len__(self):
        return len(self.__groups)

    def __iter__(self):
        for group in self.__groups:
            yield group

    def __get_groups(self):
        log.debug("FreeNAS_LDAP_Groups.__get_groups: enter")

        if (self.flags & FLAGS_CACHE_READ_GROUP) and self.__loaded('g'):
            log.debug("FreeNAS_LDAP_Groups.__get_groups: groups in cache")
            log.debug("FreeNAS_LDAP_Groups.__get_groups: leave")
            self.__groups = self.__gcache
            return

        self.attributes = ['cn']

        ldap_groups = None
        if (self.flags & FLAGS_CACHE_READ_GROUP) and self.__loaded('dg'):
            log.debug("FreeNAS_LDAP_Groups.__get_groups: LDAP groups in cache")
            ldap_groups = self.__dgcache

        else:
            log.debug("FreeNAS_LDAP_Groups.__get_groups: LDAP groups not in cache")
            ldap_groups = self.get_groups()

        for g in ldap_groups:
            CN = str(g[0])
            if self.flags & FLAGS_CACHE_WRITE_GROUP:
                self.__dgcache[CN] = g

            g = g[1]
            cn = str(g['cn'][0])
            try:
                gr = grp.getgrnam(cn)

            except:
                continue

            self.__groups.append(gr)

            if self.flags & FLAGS_CACHE_WRITE_GROUP:
                self.__gcache[cn] = gr

            gr = None

        if self.flags & FLAGS_CACHE_WRITE_GROUP:
            self.__loaded('g', True)
            self.__loaded('dg', True)

        log.debug("FreeNAS_LDAP_Groups.__get_groups: leave")


class FreeNAS_ActiveDirectory_Groups(FreeNAS_ActiveDirectory):
    def __init__(self, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Groups.__init__: enter")

        super(FreeNAS_ActiveDirectory_Groups, self).__init__(**kwargs)

        self.__groups = {}
        self.__gcache = {}
        self.__dgcache = {}

        if kwargs.has_key('netbiosname') and kwargs['netbiosname']:
            self.__domains = self.get_domains(netbiosname=kwargs['netbiosname'])
        else:
            self.__domains = self.get_domains()

        if (self.flags & FLAGS_CACHE_READ_GROUP) or \
            (self.flags & FLAGS_CACHE_WRITE_GROUP):
            for d in self.__domains:
                n = d['nETBIOSName']
                self.__gcache[n] = FreeNAS_GroupCache(dir=n)
                self.__dgcache[n] = FreeNAS_Directory_GroupCache(dir=n)

        self.__get_groups()

        log.debug("FreeNAS_ActiveDirectory_Groups.__init__: leave")

    def __loaded(self, index, netbiosname=None, write=False):
        ret = False

        paths = {}
        gcachedir = self.__gcache[netbiosname].cachedir
        paths['g'] = os.path.join(gcachedir, ".gl")

        dgcachedir = self.__dgcache[netbiosname].cachedir 
        paths['dg'] = os.path.join(dgcachedir, ".dgl")
   
        file = None
        try:
            file = paths[index]

        except:
            file = None

        if file and write:
            try:
                with open(file, 'w+') as f:
                    f.close()
                ret = True 

            except:
                ret = False

        elif file:
            if os.access(file, os.F_OK):
                ret = True

        return ret

    def __len__(self):
        length = 0
        for d in self.__domains:
            length += len(self.__groups[d['nETBIOSName']])
        return length

    def __iter__(self):
        for d in self.__domains:
            for group in self.__groups[d['nETBIOSName']]:
                yield group

    def __get_groups(self):
        log.debug("FreeNAS_ActiveDirectory_Groups.__get_groups: enter")

        if (self.flags & FLAGS_CACHE_READ_GROUP):
            dcount = len(self.__domains)
            count = 0

            for d in self.__domains:
                n = d['nETBIOSName']
                if self.__loaded('u', n):
                    self.__groups[n] = self.__gcache[n]
                    count += 1

            if count == dcount:
                log.debug("FreeNAS_ActiveDirectory_Groups.__get_groups: groups in cache")
                log.debug("FreeNAS_ActiveDirectory_Groups.__get_groups: leave")
                return

        self._save()
        for d in self.__domains:
            n = d['nETBIOSName']
            self.__groups[n] = []

            dcs = self.get_domain_controllers(d['dnsRoot'])
            (self.host, self.port) = self.dc_connect(d['dnsRoot'], self.binddn, self.bindpw)

            self.basedn = d['nCName']
            self.attributes = ['sAMAccountName']
            self.pagesize = FREENAS_LDAP_PAGESIZE

            self.close()
            self.open()

            if (self.flags & FLAGS_CACHE_READ_GROUP) and self.__loaded('dg', n):
                log.debug("FreeNAS_ActiveDirectory_Groups.__get_groups: "
                    "AD [%s] groups in cache", n)
                ad_groups = self.__dgcache[n]

            else:
                log.debug("FreeNAS_ActiveDirectory_Groups.__get_groups: "
                    "AD [%s] groups not in cache", n)
                ad_groups = self.get_groups()

            for g in ad_groups:
                sAMAccountName = g[1]['sAMAccountName'][0]
                if self.default or self.unix:
                    sAMAccountName = str("%s%s%s" % (n, FREENAS_AD_SEPARATOR, sAMAccountName))

                if self.flags & FLAGS_CACHE_WRITE_GROUP:
                    self.__dgcache[n][sAMAccountName.upper()] = g

                try:
                    gr = grp.getgrnam(sAMAccountName)

                except:
                    continue

                self.__groups[n].append(gr)
                if self.flags & FLAGS_CACHE_WRITE_GROUP:
                    self.__gcache[n][sAMAccountName.upper()] = gr

                gr = None

            if self.flags & FLAGS_CACHE_WRITE_GROUP:
                self.__loaded('g', n, True)
                self.__loaded('dg', n, True)

        self._restore()
        log.debug("FreeNAS_ActiveDirectory_Groups.__get_groups: leave")


class FreeNAS_Directory_Groups(object):
    def __new__(cls, **kwargs):
        log.debug("FreeNAS_Directory_Groups.__new__: enter")

        dflags = 0
        if kwargs.has_key('dflags'):
            dflags = kwargs['dflags']

        obj = None
        if dflags & FLAGS_LDAP_ENABLED:
            obj = FreeNAS_LDAP_Groups(**kwargs)

        elif dflags & FLAGS_AD_ENABLED:
            obj = FreeNAS_ActiveDirectory_Groups(**kwargs)

        log.debug("FreeNAS_Directory_Groups.__new__: leave")
        return obj


class FreeNAS_LDAP_Group(FreeNAS_LDAP):
    def __init__(self, group, **kwargs):
        log.debug("FreeNAS_LDAP_Group.__init__: enter")
        log.debug("FreeNAS_LDAP_Group.__init__: group = %s", group)

        if group:
            group = group.encode('utf-8')

        super(FreeNAS_LDAP_Group, self).__init__(**kwargs)

        if (self.flags & FLAGS_CACHE_READ_GROUP) or \
            (self.flags & FLAGS_CACHE_WRITE_GROUP):
            self.__gcache = FreeNAS_GroupCache()
            self.__dgcache = FreeNAS_Directory_GroupCache()
            if self.groupsuffix and self.basedn:
                self.__key = str("cn=%s,%s,%s" % (group, self.groupsuffix, self.basedn))
            elif self.basedn:
                self.__key = str("cn=%s,%s" % (group, self.basedn))

        self._gr = None
        if group:
            self.__get_group(group)

        log.debug("FreeNAS_LDAP_Group.__init__: leave")

    def __get_group(self, group):
        log.debug("FreeNAS_LDAP_Group.__get_group: enter")
        log.debug("FreeNAS_LDAP_Group.__get_group: group = %s", group)

        gr = None
        self.attributes = ['cn']

        if (self.flags & FLAGS_CACHE_READ_GROUP) and self.__gcache.has_key(group):
            log.debug("FreeNAS_LDAP_Group.__get_group: group in cache")
            return self.__gcache[group]

        if (self.flags & FLAGS_CACHE_READ_GROUP) and self.__dgcache.has_key(self.__key):
            log.debug("FreeNAS_LDAP_Group.__get_group: LDAP group in cache")
            ldap_group = self.__dgcache[self.__key]

        else:
            log.debug("FreeNAS_LDAP_Group.__get_group: LDAP group not in cache")
            ldap_group = self.get_group(group)

        if ldap_group:
            try:
                gr = grp.getgrnam(ldap_group[1]['cn'][0])

            except:
                gr = None

        else:
            if type(group) in (types.IntType, types.LongType) or group.isdigit():
                try:
                    gr = grp.getgrgid(group)

                except:
                    gr = None

            else:
                try:
                    gr = grp.getgrnam(group)

                except:
                    gr = None

        if (self.flags & FLAGS_CACHE_WRITE_GROUP) and gr:
            self.__gcache[group] = gr
            self.__dgcache[self.__key] = ldap_group

        self._gr = gr
        log.debug("FreeNAS_LDAP_Group.__get_group: leave")


class FreeNAS_ActiveDirectory_Group(FreeNAS_ActiveDirectory):
    def __new__(cls, group, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Group.__new__: enter")
        log.debug("FreeNAS_ActiveDirectory_Group.__new__: group = %s", group)

        obj = None
        if group:
            group = group.encode('utf-8')
            parts = group.split(FREENAS_AD_SEPARATOR)
            if len(parts) > 1 and parts[1]:
                obj = super(FreeNAS_ActiveDirectory_Group, cls).__new__(cls, **kwargs)

        log.debug("FreeNAS_ActiveDirectory_Group.__new__: leave")
        return obj

    def __init__(self, group, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_Group.__init__: enter")
        log.debug("FreeNAS_ActiveDirectory_Group.__init__: group = %s", group)

        parts = group.split(FREENAS_AD_SEPARATOR)
        netbiosname = parts[0]
        group = parts[1]

        self._gr = None

        kwargs['netbiosname'] = netbiosname
        super(FreeNAS_ActiveDirectory_Group, self).__init__(**kwargs)

        if (self.flags & FLAGS_CACHE_READ_GROUP) or \
            (self.flags & FLAGS_CACHE_WRITE_GROUP):
            self.__gcache = FreeNAS_GroupCache()
            self.__dgcache = FreeNAS_Directory_GroupCache(dir=netbiosname)
            self.__key = str(("%s%s%s" % (netbiosname, FREENAS_AD_SEPARATOR, group)).upper())

        self.__get_group(group, netbiosname)

        log.debug("FreeNAS_ActiveDirectory_Group.__init__: leave")

    def __get_group(self, group, netbiosname):
        log.debug("FreeNAS_ActiveDirectory_Group.__get_group: enter")
        log.debug("FreeNAS_ActiveDirectory_Group.__get_group: group = %s", group)
        log.debug("FreeNAS_ActiveDirectory_Group.__get_group: netbiosname = %s", netbiosname)

        if (self.flags & FLAGS_CACHE_READ_GROUP) and self.__gcache.has_key(group):
            log.debug("FreeNAS_ActiveDirectory_User.__get_group: group in cache")
            return self.__gcache[group]

        g = gr = None
        self.basedn = self.get_baseDN()
        self.attributes = ['sAMAccountName']

        if (self.flags & FLAGS_CACHE_READ_GROUP) and self.__dgcache.has_key(self.__key):
            log.debug("FreeNAS_ActiveDirectory_Group.__get_group: AD group in cache")
            ad_group = self.__dgcache[self.__key]

        else:
            log.debug("FreeNAS_ActiveDirectory_Group.__get_group: AD group not in cache")
            ad_group = self.get_group(group)

        if self.default or self.unix:
            g = ad_group[1]['sAMAccountName'][0] if ad_group else group
        else:
            g = "%s%s%s" % (netbiosname, FREENAS_AD_SEPARATOR,
                ad_group[1]['sAMAccountName'][0] if ad_group else group)

        try:
            gr = grp.getgrnam(g)

        except:
            gr = None

        if (self.flags & FLAGS_CACHE_WRITE_GROUP) and gr:
            self.__gcache[group] = gr
            self.__dgcache[self.__key] = ad_group

        self._gr = gr
        log.debug("FreeNAS_ActiveDirectory_Group.__get_group: leave")


class FreeNAS_Directory_Group(object):
    def __new__(cls, group, **kwargs):
        log.debug("FreeNAS_Directory_Group.__new__: enter")
        log.debug("FreeNAS_Directory_Group.__new__: group = %s", group)

        dflags = 0
        if kwargs.has_key('dflags'):
            dflags = kwargs['dflags']

        obj = None
        if dflags & FLAGS_LDAP_ENABLED:
            obj = FreeNAS_LDAP_Group(group, **kwargs)

        elif dflags & FLAGS_AD_ENABLED:
            obj = FreeNAS_ActiveDirectory_Group(group, **kwargs)

        if obj and obj._gr is None:
            obj = None

        log.debug("FreeNAS_Directory_Group.__new__: leave")
        return obj


class FreeNAS_LDAP_User(FreeNAS_LDAP):
    def __init__(self, user, **kwargs):
        log.debug("FreeNAS_LDAP_User.__init__: enter")
        log.debug("FreeNAS_LDAP_User.__init__: user = %s", user)

        if user:
            user = user.encode('utf-8')

        super(FreeNAS_LDAP_User, self).__init__(**kwargs)

        if (self.flags & FLAGS_CACHE_READ_USER) or \
            (self.flags & FLAGS_CACHE_WRITE_USER):
            self.__ucache = FreeNAS_UserCache()
            self.__ducache = FreeNAS_Directory_UserCache()
            if self.usersuffix and self.basedn:
                self.__key = str("uid=%s,%s,%s" % (user, self.usersuffix, self.basedn))
            elif self.basedn:
                self.__key = str("uid=%s,%s" % (user, self.basedn))

        self._pw = None
        if user:
            self.__get_user(user)

        log.debug("FreeNAS_LDAP_User.__init__: leave")

    def __get_user(self, user):
        log.debug("FreeNAS_LDAP_User.__get_user: enter")
        log.debug("FreeNAS_LDAP_User.__get_user: user = %s", user)

        pw = None
        self.attributes = ['uid']

        if (self.flags & FLAGS_CACHE_READ_USER) and self.__ucache.has_key(user):
            log.debug("FreeNAS_LDAP_User.__get_user: user in cache")
            return self.__ucache[user]

        if (self.flags & FLAGS_CACHE_READ_USER) and self.__ducache.has_key(self.__key):
            log.debug("FreeNAS_LDAP_User.__get_user: LDAP user in cache")
            ldap_user = self.__ducache[self.__key]

        else:
            log.debug("FreeNAS_LDAP_User.__get_user: LDAP user not in cache")
            ldap_user = self.get_user(user)

        if ldap_user:
            self.__CN = ldap_user[0]
            uid = ldap_user[1]['uid'][0]
            try:
                pw = pwd.getpwnam(uid)

            except:
                pw = None

        else:
            if type(user) in (types.IntType, types.LongType) or user.isdigit():
                try:
                    pw = pwd.getpwuid(user)

                except:
                    pw = None

            else:
                try:
                    pw = pwd.getpwnam(user)

                except:
                    pw = None

        if (self.flags & FLAGS_CACHE_WRITE_USER) and pw:
            self.__ucache[user] = pw
            self.__ducache[self.__key] = ldap_user

        self._pw = pw
        log.debug("FreeNAS_LDAP_User.__get_user: leave")


class FreeNAS_ActiveDirectory_User(FreeNAS_ActiveDirectory):
    def __new__(cls, user, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_User.__new__: enter")
        log.debug("FreeNAS_ActiveDirectory_User.__new__: user = %s", user)

        obj = None
        if user:
            user = user.encode('utf-8')
            parts = user.split(FREENAS_AD_SEPARATOR)
            if len(parts) > 1 and parts[1]:
                obj = super(FreeNAS_ActiveDirectory_User, cls).__new__(cls, **kwargs)

        log.debug("FreeNAS_ActiveDirectory_User.__new__: leave")
        return obj

    def __init__(self, user, **kwargs):
        log.debug("FreeNAS_ActiveDirectory_User.__init__: enter")
        log.debug("FreeNAS_ActiveDirectory_User.__init__: user = %s", user)

        parts = user.split(FREENAS_AD_SEPARATOR)
        netbiosname = parts[0]
        user = parts[1]

        self._pw = None

        kwargs['netbiosname'] = netbiosname
        super(FreeNAS_ActiveDirectory_User, self).__init__(**kwargs)

        if (self.flags & FLAGS_CACHE_READ_USER) or \
            (self.flags & FLAGS_CACHE_WRITE_USER):
            self.__ucache = FreeNAS_UserCache()
            self.__ducache = FreeNAS_Directory_UserCache(dir=netbiosname)
            self.__key = str(("%s%s%s" % (netbiosname, FREENAS_AD_SEPARATOR, user)).upper())

        self.__get_user(user, netbiosname)

        log.debug("FreeNAS_ActiveDirectory_User.__init__: leave")

    def __get_user(self, user, netbiosname):
        log.debug("FreeNAS_ActiveDirectory_User.__get_user: enter")
        log.debug("FreeNAS_ActiveDirectory_User.__get_user: user = %s", user)
        log.debug("FreeNAS_ActiveDirectory_User.__get_user: netbiosname = %s", netbiosname)

        if (self.flags & FLAGS_CACHE_READ_USER) and self.__ucache.has_key(user):
            log.debug("FreeNAS_ActiveDirectory_User.__get_user: user in cache")
            return self.__ucache[user]

        pw = None
        self.basedn = self.get_baseDN()
        self.attributes = ['sAMAccountName']

        if (self.flags & FLAGS_CACHE_READ_USER) and self.__ducache.has_key(self.__key):
            log.debug("FreeNAS_ActiveDirectory_User.__get_user: AD user in cache")
            ad_user = self.__ducache[self.__key]

        else:
            log.debug("FreeNAS_ActiveDirectory_User.__get_user: AD user not in cache")
            ad_user = self.get_user(user)

        if self.default or self.unix:
            u = ad_user[1]['sAMAccountName'][0] if ad_user else user
        else:
            u = "%s%s%s" % (netbiosname, FREENAS_AD_SEPARATOR,
                ad_user[1]['sAMAccountName'][0] if ad_user else user)

        try:
            pw = pwd.getpwnam(u)

        except:
            pw = None

        if (self.flags & FLAGS_CACHE_WRITE_USER) and pw:
            self.__ucache[user] = pw
            self.__ducache[self.__key] = ad_user

        self._pw = pw
        log.debug("FreeNAS_ActiveDirectory_User.__get_user: leave")


class FreeNAS_Directory_User(object):
    def __new__(cls, user, **kwargs):
        log.debug("FreeNAS_Directory_User.__new__: enter")
        log.debug("FreeNAS_Directory_User.__new__: user = %s", user)

        dflags = 0
        if kwargs.has_key('dflags'):
            dflags = kwargs['dflags']

        obj = None
        if dflags & FLAGS_LDAP_ENABLED:
            obj = FreeNAS_LDAP_User(user, **kwargs)

        elif dflags & FLAGS_AD_ENABLED:
            obj = FreeNAS_ActiveDirectory_User(user, **kwargs)

        if obj and obj._pw is None:
            obj = None

        log.debug("FreeNAS_Directory_User.__new__: leave")
        return obj
