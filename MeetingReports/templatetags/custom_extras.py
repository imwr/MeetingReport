from django import template

register = template.Library()


class SetVarNode(template.Node):
    def __init__(self, var_name, var_value):
        self.var_name = var_name
        self.var_value = var_value

    def render(self, context):
        try:
            value = template.Variable(self.var_value).resolve(context)
        except template.VariableDoesNotExist:
            value = ""
        context[self.var_name] = value
        return u""


@register.tag
def set(parser, token):
    """
        {% set <var_name>  = <var_value> %}
    """
    parts = token.split_contents()
    if len(parts) < 4:
        raise template.TemplateSyntaxError("'set' tag must be of the form:  {% set <var_name>  = <var_value> %}")
    return SetVarNode(parts[1], parts[3])


@register.filter
def user_email(users):
    return ",  ".join([user.username + '<' + user.email + '>' for user in users])


@register.filter
def user_report(content):
    return "<li>" + "</li><li>".join(content.split(",")) + "</li>"
