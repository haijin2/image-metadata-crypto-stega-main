from django.urls import path
from imetadata import views  
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Home route, redirects to the encryption page
    path('', views.home_view, name='home'),  # Home page for the root URL

    # Encryption and decryption views
    path('encrypt/', views.encrypt_view, name='encrypt'),
    path('decrypt/', views.decrypt_view, name='decrypt'),
    path('download/<str:file_path>/', views.download_file, name='download_file'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)