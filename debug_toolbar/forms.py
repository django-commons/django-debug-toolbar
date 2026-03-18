import json

from django import forms
from django.core import signing
from django.core.exceptions import ValidationError

from debug_toolbar.sanitize import force_str


class SignedDataForm(forms.Form):
    """Helper form that wraps a form to validate its contents on post.

    class PanelForm(forms.Form):
        # fields

    On render:
        form = SignedDataForm(initial=PanelForm(initial=data).initial)

    On POST:
        signed_form = SignedDataForm(request.POST)
        if signed_form.is_valid():
            panel_form = PanelForm(signed_form.verified_data)
            if panel_form.is_valid():
                # Success
    """

    salt = "django_debug_toolbar"
    signed = forms.CharField(required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop("initial", None)
        if initial:
            initial = {"signed": self.sign(initial)}
        super().__init__(*args, initial=initial, **kwargs)

    def clean_signed(self):
        try:
            verified = json.loads(
                signing.Signer(salt=self.salt).unsign(self.cleaned_data["signed"])
            )
            return verified
        except signing.BadSignature as exc:
            raise ValidationError("Bad signature") from exc

    def verified_data(self):
        return self.is_valid() and self.cleaned_data["signed"]

    @classmethod
    def sign(cls, data):
        return signing.Signer(salt=cls.salt).sign(
            json.dumps({key: force_str(value) for key, value in data.items()})
        )
