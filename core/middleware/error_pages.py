from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin

class ErrorPagesMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        content_type = response.get('Content-Type', '')
        if 'text/html' not in content_type:
            return response

        status_code = response.status_code
        if status_code in [400, 401, 403, 404, 500]:
            template_name = f'core/errors/{status_code}.html'
            return render(request, template_name, status=status_code)
            
        return response
