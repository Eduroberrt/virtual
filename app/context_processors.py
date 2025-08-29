from datetime import datetime

def global_context(request):
    """
    Add global context variables available to all templates
    """
    return {
        'current_year': datetime.now().year,
    }
