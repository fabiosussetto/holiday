import datetime
from django.template import Library, Node, TemplateSyntaxError
from django.contrib.staticfiles.storage import staticfiles_storage

register = Library()

@register.simple_tag
def profile_pic(user):
    output = ''
    if user.google_pic_url:
        output = '<img src="%s" class="user-pic">' % user.google_pic
    else:
        output = '<img src="%s" class="user-pic missing">' % staticfiles_storage.url('img/missing_pic.gif')
    return output
    
@register.simple_tag(takes_context=True)
def topnav_active(context, section):
    try:
        return 'active' if context['main_section'] == section else ''
    except KeyError:
        return ''

@register.simple_tag
def in_date_range(requests, week_days):
    output = []
    today = datetime.datetime.now().date()
    for day in week_days:
        classes = ['day']
        has = False
        if day == today:
            classes.append('today')
        elif day < today:
            classes.append('past')
            
        for obj in requests:
            if day >= obj.start_date and day <= obj.end_date:
                classes.extend(['request', obj.status])
                if day == obj.start_date:
                    classes.append('first')
                elif day == obj.end_date:
                    classes.append('last')
        output.append('<td data-date="%s" class="%s"><span></span></td>' % (day.strftime('%Y-%m-%d'), ' '.join(classes)))
            
    return ''.join(output)
    
    
class RangeNode(Node):
    def __init__(self, range_args, context_name):
        self.range_args = range_args
        self.context_name = context_name

    def render(self, context):
        context[self.context_name] = range(*self.range_args)
        return ""
        
@register.tag
def mkrange(parser, token):
    """
    Accepts the same arguments as the 'range' builtin and creates
    a list containing the result of 'range'.
    
    Syntax:
        {% mkrange [start,] stop[, step] as context_name %}

    For example:
        {% mkrange 5 10 2 as some_range %}
        {% for i in some_range %}
          {{ i }}: Something I want to repeat\n
        {% endfor %}
    
    Produces:
        5: Something I want to repeat 
        7: Something I want to repeat 
        9: Something I want to repeat 
    """

    tokens = token.split_contents()
    fnctl = tokens.pop(0)

    def error():
        raise TemplateSyntaxError, "%s accepts the syntax: {%% %s [start,] " +\
                "stop[, step] as context_name %%}, where 'start', 'stop' " +\
                "and 'step' must all be integers." %(fnctl, fnctl)

    range_args = []
    while True:
        if len(tokens) < 2:
            error()

        token = tokens.pop(0)

        if token == "as":
            break

        if not token.isdigit():
            error()
        range_args.append(int(token))
    
    if len(tokens) != 1:
        error()

    context_name = tokens.pop()

    return RangeNode(range_args, context_name)