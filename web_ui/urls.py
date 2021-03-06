from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, logout
from main_menu import admin_custom as admin
from django.views.generic.base import RedirectView
#from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page' : '/accounts/login'}),
    (r'^$', 'main_menu.views.index'),
    #(r'^index/$',  RedirectView.as_view(url='localhost:8000'),'main_menu.views.index'),
    #(r'^admin_page/$', 'main_menu.views.admin_page'),
    (r'^user/$', 'main_menu.views.user_page'),
    (r'^auth_token/$', 'main_menu.views.auth_token'),
    (r'^token_data/$', 'main_menu.views.token_data'),
    #(r'^admin/$', 'main_menu.views.admin_page'),
    (r'^index/$','main_menu.views.index'),
    (r'^index/demo/$','main_menu.views.demo'),
    (r'^demo/$','main_menu.views.demo'),
    (r'/admin/$', 'main_menu.views.admin_page'),
    (r'^demo/admin/$', 'main_menu.views.admin_page'),
    (r'^auth_token_user/$', 'main_menu.views.auth_token_user'),
    (r'^index/demo/user/$', 'main_menu.views.user_page'),
    (r'^demo/user/$', 'main_menu.views.user_page'),
    (r'/user_price/$', 'main_menu.views.user_page_calculate_price'),
    (r'/user_periodic/$', 'main_menu.views.user_page_periodic_price'),
    #(r'/calculate_price/$', 'main_menu.views.calculate_price'),
    #(r'^admin/main_menu/stackuser/calculate_price$','main_menu.admin.calculate_price'),
    #(r'^js/jquery-1.11.0.min.js/$', include("static/js/jquery-1.11.0.min.js")),
    #(r'^js/jquery-ui-1.10.4.min.js/$', include("static/js/jquery-ui-1.10.4.min.js")),
    #(r'^js/ui.js/$', include("static/js/ui.js")),
    #(r'^/define_pricing/?ct=(?P<ct>\d+)/$', 'main_menu.views.define_pricing'),
    
)
