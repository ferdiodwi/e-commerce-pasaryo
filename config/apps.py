from django.contrib.admin.apps import AdminConfig


class RoleAdminConfig(AdminConfig):
    default_site = "config.admin.RoleAdminSite"