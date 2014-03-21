import logging

from freenasUI.freeadmin.apppool import appPool

log = logging.getLogger('freeadmin.hook')


class HookMetaclass(type):

    def __new__(cls, name, bases, attrs):
        base = type(name, (object, ), attrs)
        if attrs.get('__hook_reverse_order__', None) is not False:
            bases = list(bases) + [base]
        else:
            bases = [base] + list(bases)
        appPool.hook_class_new(name, bases, attrs)
        new_class = type(name, tuple(bases), {})
        return new_class


class AppHook(object):

    name = None

    def base_css(self, request):
        """
        List of css files to be appended to the base template
        Path within STATIC_URL
        """
        return []

    def base_js(self, request):
        """
        List of javascript files to be appended to the base template
        Path within STATIC_URL
        """
        return []

    def top_menu(self, request):
        """
        Items to be placed in the top menu bar

        Returns: list(dict)
          - id - id of the DOM node
          - name - name to be displayed
          - icon - path to the icon, within STATIC_URL
          - onclick - javascript code to run on mouse click
          - weight - order of the menu
          - align - "left, right" (optional)
          - img - content to be placed above the name
        """
        return []

    def system_menu(self, request):
        """
        Items to be placed in the system info screen

        Returns: list(dict)
         - name: name to be displayed
         - value: value to show
        """
        return []

    """
    def hook_app_index_<app>(self, request):
        '''
        Hook called to get a view to run instead of the default index
        '''
        pass
    """

    """
    def hook_app_tabs_<app>(self, request):
        '''
        Hook called to get a list of additional tabs for an app
        '''
        pass
    """

    """
    def hook_datagrid_actions_<AdminName>(self, admin, actions):
        '''
        Hook called on generation of action buttons (bottom) for the datagrid
        '''
        pass
    """

    """
    def hook_datagrid_buttons_<AdminName>(self, admin):
        '''
        Hook called on generation of static buttons (top) for the datagrid
        '''
        pass
    """

    """
    def hook_feature_disabled_<name>(self):
        '''
        Hook called to check weather a given feature is disabled
        '''
        pass
    """

    """
    def hook_form_buttons_<FormName>(self, form, *args, **kwargs):
        '''
        Hook called to get extra buttons to be placed at the end of the form
        '''
        pass
    """

    """
    def hook_form_done_<FormName>(self, form, request, events):
        '''
        Hook called on form done method, after save and validation
        '''
        pass
    """

    """
    def hook_form_delete_<FormName>(self, form, request, events):
        '''
        Hook called on form delete method
        '''
        pass
    """

    """
    def hook_form_init_<FormName>(self, form, *args, **kwargs):
        '''
        Hook called on form __init__ method, after django.forms.Form
        '''
        pass
    """

    """
    def hook_model_new_<Model>(self, bases, attrs):
        '''
        Hook called on model meta class before __new__
        '''
        pass
    """

    """
    def hook_nav_init_<app>(self, app, tree_roots, nav, request):
        '''
        Hook called on bundle method of the REST resource
        '''
        pass
    """

    """
    def hook_resource_bundle_<ResourceName>(self, resource, bundle):
        '''
        Hook called on bundle method of the REST resource
        '''
        pass
    """

    """
    def hook_tool_run_<toolname>(self):
        '''
        Hook called when a tool is ran
        '''
        pass
    """
