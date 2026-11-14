from django.contrib.admin.apps import AdminConfig

class StudioAdminConfig(AdminConfig):
    default_site = 'core.admin_site.StudioAdminSite'
