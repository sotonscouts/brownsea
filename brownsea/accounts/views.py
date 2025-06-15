from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.auth.views import LoginView as DjangoLoginView


class LoginView(DjangoLoginView):
    template_name = "pages/accounts/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        form.helper = FormHelper()
        form.helper.form_method = "post"
        form.helper.add_input(Submit("submit", "Login"))
        return context
