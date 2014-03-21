from django.utils.translation import ugettext as _

from freenasUI.api.resources import (
    FTPResourceMixin, ISCSIPortalResourceMixin, ISCSITargetResourceMixin,
    ISCSITargetExtentResourceMixin, ISCSITargetToExtentResourceMixin,
    NFSResourceMixin, ServicesResourceMixin
)
from freenasUI.freeadmin.options import BaseFreeAdmin
from freenasUI.freeadmin.site import site
from freenasUI.services import models


class ServicesFAdmin(BaseFreeAdmin):

    resource_mixin = ServicesResourceMixin


class FTPFAdmin(BaseFreeAdmin):

    resource_mixin = FTPResourceMixin
    deletable = False
    icon_model = "FTPIcon"
    advanced_fields = (
        'ftp_filemask',
        'ftp_dirmask',
        'ftp_fxp',
        'ftp_ident',
        'ftp_passiveportsmin',
        'ftp_passiveportsmax',
        'ftp_localuserbw',
        'ftp_localuserdlbw',
        'ftp_anonuserbw',
        'ftp_anonuserdlbw',
        'ftp_tls',
        'ftp_tls_policy',
        'ftp_tls_opt_allow_client_renegotiations',
        'ftp_tls_opt_allow_dot_login',
        'ftp_tls_opt_allow_per_user',
        'ftp_tls_opt_common_name_required',
        'ftp_tls_opt_enable_diags',
        'ftp_tls_opt_export_cert_data',
        'ftp_tls_opt_no_cert_request',
        'ftp_tls_opt_no_empty_fragments',
        'ftp_tls_opt_no_session_reuse_required',
        'ftp_tls_opt_stdenvvars',
        'ftp_tls_opt_use_implicit_ssl',
        'ftp_tls_opt_dns_name_required',
        'ftp_tls_opt_ip_address_required',
        'ftp_ssltls_certfile',
        'ftp_options',
    )


class ISCSITargetFAdmin(BaseFreeAdmin):

    menu_child_of = "services.ISCSI"
    icon_object = u"TargetIcon"
    icon_model = u"TargetIcon"
    icon_add = u"AddTargetIcon"
    icon_view = u"ViewAllTargetsIcon"

    exclude_fields = (
        'id',
        'iscsi_target_initialdigest',
        'iscsi_target_type',
    )

    resource_mixin = ISCSITargetResourceMixin


class ISCSIPortalFAdmin(BaseFreeAdmin):

    menu_child_of = "services.ISCSI"
    icon_object = u"PortalIcon"
    icon_model = u"PortalIcon"
    icon_add = u"AddPortalIcon"
    icon_view = u"ViewAllPortalsIcon"
    inlines = [
        {
            'form': 'iSCSITargetPortalIPForm',
            'prefix': 'portalip_set',
        },
    ]

    resource_mixin = ISCSIPortalResourceMixin

    def get_datagrid_columns(self):
        columns = super(ISCSIPortalFAdmin, self).get_datagrid_columns()
        columns.insert(1, {
            'name': 'iscsi_target_portal_ips',
            'label': _('Listen'),
            'sortable': False,
        })
        return columns


class ISCSIAuthCredentialFAdmin(BaseFreeAdmin):

    menu_child_of = "services.ISCSI"
    icon_object = u"AuthorizedAccessIcon"
    icon_model = u"AuthorizedAccessIcon"
    icon_add = u"AddAuthorizedAccessIcon"
    icon_view = u"ViewAllAuthorizedAccessIcon"

    exclude_fields = (
        'id',
        'iscsi_target_auth_secret',
        'iscsi_target_auth_peersecret',
        )

    resource_name = 'services/iscsi/authcredential'


class ISCSITargetToExtentFAdmin(BaseFreeAdmin):

    menu_child_of = "services.ISCSI"
    icon_object = u"TargetExtentIcon"
    icon_model = u"TargetExtentIcon"
    icon_add = u"AddTargetExtentIcon"
    icon_view = u"ViewAllTargetExtentsIcon"

    resource_mixin = ISCSITargetToExtentResourceMixin


class ISCSITargetExtentFAdmin(BaseFreeAdmin):

    delete_form = "ExtentDelete"
    delete_form_filter = {'iscsi_target_extent_type__exact': 'File'}
    menu_child_of = "services.ISCSI"
    icon_object = u"ExtentIcon"
    icon_model = u"ExtentIcon"
    icon_add = u"AddExtentIcon"
    icon_view = u"ViewAllExtentsIcon"

    resource_mixin = ISCSITargetExtentResourceMixin

    exclude_fields = (
        'id',
        'iscsi_target_extent_filesize',
    )


class NFSFAdmin(BaseFreeAdmin):

    resource_mixin = NFSResourceMixin
    deletable = False
    icon_model = 'NFSIcon'


site.register(models.FTP, FTPFAdmin)
site.register(models.iSCSITarget, ISCSITargetFAdmin)
site.register(models.iSCSITargetPortal, ISCSIPortalFAdmin)
site.register(models.iSCSITargetAuthCredential, ISCSIAuthCredentialFAdmin)
site.register(models.iSCSITargetToExtent, ISCSITargetToExtentFAdmin)
site.register(models.iSCSITargetExtent, ISCSITargetExtentFAdmin)
site.register(models.NFS, NFSFAdmin)
site.register(models.services, ServicesFAdmin)
