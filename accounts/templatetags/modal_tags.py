"""Custom template tags for rendering shared modal components."""

from django import template

register = template.Library()


@register.inclusion_tag("accounts/components/modal_wrapper.html", takes_context=True)
def render_modal(context, **modal_options):
    """Render a modal wrapper with the provided keyword options."""

    required_keys = {
        "modal_data_attr",
        "modal_title",
        "modal_title_id",
        "modal_body_template",
    }
    missing_keys = required_keys - modal_options.keys()
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise ValueError(f"Missing modal option(s): {missing}")

    new_context = context.flatten()
    new_context.update(
        {
            **modal_options,
            "modal_should_show": modal_options.get("modal_should_show", False),
        }
    )
    return new_context
