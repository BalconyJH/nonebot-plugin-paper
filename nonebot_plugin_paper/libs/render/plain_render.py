from aioarxiv.models import Paper


class Render:
    pass


async def render_paper(paper: Paper):
    """
    Formats the paper information into a text message.

    Args:
        paper: The paper object to format.

    Returns:
        The formatted text message.
    """
    authors = ", ".join([author.name for author in paper.info.authors])
    published_date = paper.info.published.strftime("%Y-%m-%d")
    updated_date = paper.info.updated.strftime("%Y-%m-%d")
    summary = (
        f"{paper.info.summary[:250]}..."
        if len(paper.info.summary) > 200
        else paper.info.summary
    )

    template = (
        f"📄 Title: {paper.info.title}\n"
        f"👥 Authors: {authors}\n"
        f"🏷️ Categories: {paper.info.categories.primary.term}\n"
        f"📅 Published Date: {published_date}\n"
        f"🔄 Updated Date: {updated_date}\n"
        f"📝 Summary: {summary}\n"
    )

    if paper.doi:
        template += f"🔗 DOI: {paper.doi}\n"
    if paper.journal_ref:
        template += f"📚 Journal Reference: {paper.journal_ref}\n"
    if paper.pdf_url:
        template += f"📥 PDF Download Link: {paper.pdf_url}\n"
    if paper.comment:
        template += f"💬 Comment: {paper.comment}\n"

    return template
