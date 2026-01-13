from django.utils.html import escape
from django.http import HttpResponse

def close_html_response(platform=None, status="success", message=""):
    platform = platform or ""
    status = status or ""
    message = message or ""

    html = f"""
    <html>
        <head>
            <title>{escape(platform.upper())} Connected</title>
        </head>
        <body>
            <script>
                if (window.opener) {{
                    window.opener.postMessage(
                        {{
                            type: "{escape(platform.upper())}_CONNECTED",
                            status: "{escape(status)}",
                            message: "{escape(message)}"
                        }},
                        "*"
                    );
                }}
                window.close();
            </script>

            <p>{escape(platform)} connected successfully. You may close this window.</p>
        </body>
    </html>
    """
    return HttpResponse(html)
