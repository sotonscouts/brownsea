from django.shortcuts import render


def page_types_guide(request):
    return render(request, "wagtailadmin/page_types_guide.html")
