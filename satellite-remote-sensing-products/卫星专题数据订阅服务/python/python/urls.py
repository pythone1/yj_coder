# from django.conf.urls import url
from django.urls import path
from . import main

urlpatterns = [
    # 哨兵一号影像更新
    path("s1update",main.s1Update),
    path("s2update",main.s2Update),
    path("test",main.test)
]