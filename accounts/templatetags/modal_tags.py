"""Custom template tags for rendering shared modal components."""

from django import template

register = template.Library()


@register.inclusion_tag(
    "accounts/components/modal_wrapper.html", takes_context=True
)
def render_modal(
    context,
    modal_data_attr,
    modal_title,
    modal_title_id,
    modal_body_template,
    modal_should_show=False,
):
    """Render a modal wrapper with the provided kwargs."""

    new_context = context.flatten()
    new_context.update(
        {
            "modal_data_attr": modal_data_attr,
            "modal_title": modal_title,
            "modal_title_id": modal_title_id,
            "modal_body_template": modal_body_template,
            "modal_should_show": modal_should_show,
        }
    )
    return new_context
