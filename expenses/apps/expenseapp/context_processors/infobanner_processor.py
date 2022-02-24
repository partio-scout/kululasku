from datetime import datetime
from ..models import InfoMessage

# from expenses.apps.expenseapp.models import InfoMessage


def info_message(request):
    print(222, request.path)
    if ('expense/new' in request.path):
        return {}
    now = datetime.now()
    infoMessage = InfoMessage.objects.filter(
        start_date__lte=now, end_date__gte=now).first()
    if infoMessage:
        infoMessage = infoMessage.languaged(request.LANGUAGE_CODE)
    return {
        'info_message': infoMessage
    }
