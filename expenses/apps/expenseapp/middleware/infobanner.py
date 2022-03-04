from datetime import datetime

from expenses.apps.expenseapp.models import InfoMessage


def ExpenseAppSetInfobannerMiddleware(get_response):

    def middleware(request):
        now = datetime.now()
        infoMessage = InfoMessage.objects.filter(
            start_date__lte=now, end_date__gte=now).first()
        if infoMessage:
            infoMessage = infoMessage.languaged(request.LANGUAGE_CODE)
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        response = get_response(request)
        response.context_data["info_message"] = infoMessage
        return response
    return middleware
