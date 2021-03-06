from django.conf.urls.defaults import *
from aur.models import Package

detail_dict = {
    'queryset': Package.objects.all(),
    'template_object_name': 'pkg',
}

urlpatterns = patterns('aur.views',
    url(r'^$', 'search', name='aur-main'),
    url(r'^search/$', 'search', name='aur-search'),
    url(r'^submit/$', 'submit', name='aur-submit_package'),
    url(r'^package/(?P<object_id>[\w_-]+)/comment/$', 'comment',
        name='aur-comment_on_package'),
    url(r'^package/(?P<object_id>[\w_-]+)/flag_out_of_date/$',
        'flag_out_of_date', name='aur-flag_out_of_date'),
    url(r'^package/(?P<object_id>[\w_-]+)/unflag_out_of_date/$',
        'unflag_out_of_date', name='aur-unflag_out_of_date'),
    url(r'^package/(?P<slug>[\w_-]+)/vote/$',
        'vote', name='aur-vote'),
    url(r'^package/(?P<slug>[\w_-]+)/unvote/$',
        'unvote', name='aur-unvote'),
    url(r'^package/(?P<object_id>[\w_-]+)/notify_of_updates/$',
        'notify_of_updates', name='aur-notify_of_updates'),
    url(r'^package/(?P<object_id>[\w_-]+)/denotify_of_updates/$',
        'denotify_of_updates', name='aur-denotify_of_updates'),
    (r'^api/', include('archlinux.aur.api.urls')),
    url(r'^manage_packages/$', 'manage_packages', name='aur-manage_packages'),
)

# Generic views
# These will probably be removed at a later stage
urlpatterns += patterns('django.views.generic',
    (r'^package/(?P<slug>[\w_-]+)/$', 'list_detail.object_detail',
        dict(detail_dict), 'aur-package_detail'),
)
