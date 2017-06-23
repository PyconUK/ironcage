from django.forms import widgets


class ButtonsRadio(widgets.ChoiceWidget):
    template_name = 'widgets/buttons_radio.html'


class ButtonsCheckbox(widgets.ChoiceWidget):
    allow_multiple_selected = True
    template_name = 'widgets/buttons_checkbox.html'


class EmailInput(widgets.EmailInput):
    template_name = 'widgets/email_input.html'
