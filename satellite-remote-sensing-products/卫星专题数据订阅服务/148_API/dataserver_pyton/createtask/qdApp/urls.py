from django.urls import path
from . import main

urlpatterns = [
    # 哨兵一号影像更新
    path("watersvectorize",main.watersVectorizationTask),
    path("idtwaters_satellite",main.idtWatersOnStlImageTask),
    path("idtwaters_aerial",main.idtWatersOnAerImageTask),
    path("waterqa_speconly",main.waterqaSpecOnlyTask),
    path("farmlandvectorize",main.farmlandVectorizationTask),
    path("landcovervectorize",main.landcoverVectorizationTask),
    path("s1update",main.s1UpdateTask),
    path("s2update",main.s2UpdateTask),
    path("s3update",main.s3UpdateTask),
    path("ccrsimgupdate",main.ccrsImgUpdateTask),
    path("aerialimgupdate",main.aerialImgUpdateTask),
    path("poi",main.gaodePOITask),
    path("precipitation",main.getPrecipitationTask),
    path("test",main.test)
]

