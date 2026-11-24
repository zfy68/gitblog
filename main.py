# -*- coding: utf-8 -*-
import argparse
import html
import os
import re

import markdown
from feedgen.feed import FeedGenerator
from github import Github
from lxml.etree import CDATA
from marko.ext.gfm import gfm as marko

MD_HEAD = """## Gitblog
My personal blog using issues and GitHub Actions
[RSS Feed](https://raw.githubusercontent.com/{repo_name}/master/feed.xml)
"""

BACKUP_DIR = "BACKUP"
ANCHOR_NUMBER = 5
TOP_ISSUES_LABELS = ["Top"]
TODO_ISSUES_LABELS = ["TODO"]
FRIENDS_LABELS = ["Friends"]
IGNORE_LABELS = FRIENDS_LABELS + TOP_ISSUES_LABELS + TODO_ISSUES_LABELS
READING_NOTES_LABEL = "读书笔记"
COVER_COLUMNS = 4
COVER_WALL_LIMIT = 8
QUOTE_CARD_LIMIT = 4
PLACEHOLDER_COVER = "assets/placeholder-cover.png"
# <!-- cover: URL --> wins, then assets/covers/issue-<n>.png when that file
# exists, then an image whose alt contains 封面, then the first image that
# is not an author or avatar photo.
_COVER_COMMENT_RE = re.compile(r"<!--\s*cover:\s*(\S+?)\s*-->", re.IGNORECASE)
_MD_IMAGE_RE = re.compile(
    r"!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)"
)
_HTML_IMAGE_RE = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)
_NON_COVER_ALT_KEYWORDS = ("作者", "头像", "肖像", "avatar", "portrait", "author")

FRIENDS_TABLE_HEAD = "| Name | Link | Desc | \n | ---- | ---- | ---- |\n"
FRIENDS_TABLE_TEMPLATE = "| {name} | {link} | {desc} |\n"
FRIENDS_INFO_DICT = {
    "名字": "",
    "链接": "",
    "描述": "",
}


def get_me(repo):
    # owner.login is on the repository payload (same value as
    # github.repository_owner). GITHUB_TOKEN cannot call GET /user.
    return repo.owner.login


def is_me(issue, me):
    return issue.user.login == me


def is_hearted_by_me(comment, me):
    reactions = list(comment.get_reactions())
    for r in reactions:
        if r.content == "heart" and r.user.login == me:
            return True
    return False


def _make_friend_table_string(s):
    info_dict = FRIENDS_INFO_DICT.copy()
    try:
        string_list = s.splitlines()
        # drop empty line
        string_list = [l for l in string_list if l and not l.isspace()]
        for l in string_list:
            string_info_list = re.split("：", l)
            if len(string_info_list) < 2:
                continue
            info_dict[string_info_list[0]] = string_info_list[1]
        return FRIENDS_TABLE_TEMPLATE.format(
            name=info_dict["名字"], link=info_dict["链接"], desc=info_dict["描述"]
        )
    except Exception as e:
        print(str(e))
        return


# help to covert xml vaild string
def _valid_xml_char_ordinal(c):
    codepoint = ord(c)
    # conditions ordered by presumed frequency
    return (
        0x20 <= codepoint <= 0xD7FF
        or codepoint in (0x9, 0xA, 0xD)
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )


def format_time(time):
    return str(time)[:10]


def login(token):
    return Github(token)


def get_repo(user: Github, repo: str):
    return user.get_repo(repo)


def parse_TODO(issue):
    body = issue.body.splitlines()
    todo_undone = [l for l in body if l.startswith("- [ ] ")]
    todo_done = [l for l in body if l.startswith("- [x] ")]
    # just add info all done
    if not todo_undone:
        return f"[{issue.title}]({issue.html_url}) all done", []
    return (
        f"[{issue.title}]({issue.html_url})--{len(todo_undone)} jobs to do--{len(todo_done)} jobs done",
        todo_done + todo_undone,
    )


def get_top_issues(repo):
    return repo.get_issues(labels=TOP_ISSUES_LABELS)


def get_todo_issues(repo):
    return repo.get_issues(labels=TODO_ISSUES_LABELS)


def get_repo_labels(repo):
    return [l for l in repo.get_labels()]


def get_issues_from_label(repo, label):
    return repo.get_issues(labels=(label,))


def add_issue_info(issue, md):
    time = format_time(issue.created_at)
    md.write(f"- [{issue.title}]({issue.html_url})--{time}\n")


def add_md_todo(repo, md, me):
    todo_issues = list(get_todo_issues(repo))
    if not TODO_ISSUES_LABELS or not todo_issues:
        return
    with open(md, "a+", encoding="utf-8") as md:
        md.write("## TODO\n")
        for issue in todo_issues:
            if is_me(issue, me):
                todo_title, todo_list = parse_TODO(issue)
                md.write("TODO list from " + todo_title + "\n")
                for t in todo_list:
                    md.write(t + "\n")
                # new line
                md.write("\n")


def add_md_top(repo, md, me):
    top_issues = list(get_top_issues(repo))
    if not TOP_ISSUES_LABELS or not top_issues:
        return
    with open(md, "a+", encoding="utf-8") as md:
        md.write("## 置顶文章\n")
        for issue in top_issues:
            if is_me(issue, me):
                add_issue_info(issue, md)


def add_md_firends(repo, md, me):
    s = FRIENDS_TABLE_HEAD
    friends_issues = list(repo.get_issues(labels=FRIENDS_LABELS))
    if not FRIENDS_LABELS or not friends_issues:
        return
    friends_issue_number = friends_issues[0].number
    for issue in friends_issues:
        for comment in issue.get_comments():
            if is_hearted_by_me(comment, me):
                try:
                    s += _make_friend_table_string(comment.body or "")
                except Exception as e:
                    print(str(e))
                    pass
    s = markdown.markdown(s, output_format="html", extensions=["extra"])
    with open(md, "a+", encoding="utf-8") as md:
        md.write(
            f"## [友情链接](https://github.com/{str(me)}/gitblog/issues/{friends_issue_number})\n"
        )
        md.write(s)
        md.write("\n\n")


def add_md_recent(repo, md, me, limit=5):
    count = 0
    with open(md, "a+", encoding="utf-8") as md:
        # one the issue that only one issue and delete (pyGitHub raise an exception)
        try:
            md.write("## 最近更新\n")
            for issue in repo.get_issues():
                if is_me(issue, me):
                    add_issue_info(issue, md)
                    count += 1
                    if count >= limit:
                        break
        except Exception as e:
            print(str(e))


def _is_non_cover_alt(alt):
    folded = (alt or "").lower()
    return any(word in alt or word in folded for word in _NON_COVER_ALT_KEYWORDS)


def _iter_body_images(body):
    found = []
    for match in _MD_IMAGE_RE.finditer(body):
        found.append((match.start(), match.group(1).strip(), match.group(2).strip()))
    for match in _HTML_IMAGE_RE.finditer(body):
        attrs = match.group(1)
        src_match = re.search(
            r'\bsrc\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE
        )
        if not src_match:
            src_match = re.search(r"\bsrc\s*=\s*([^\s>]+)", attrs, re.IGNORECASE)
        if not src_match:
            continue
        alt_match = re.search(
            r'\balt\s*=\s*["\']([^"\']*)["\']', attrs, re.IGNORECASE
        )
        alt = alt_match.group(1).strip() if alt_match else ""
        found.append((match.start(), alt, src_match.group(1).strip()))
    found.sort(key=lambda item: item[0])
    return [(alt, url) for _, alt, url in found]


def extract_cover_url(body):
    if not body:
        return None
    comment = _COVER_COMMENT_RE.search(body)
    if comment:
        return comment.group(1)
    images = _iter_body_images(body)
    for alt, url in images:
        if "封面" in alt and not _is_non_cover_alt(alt):
            return url
    for alt, url in images:
        if not _is_non_cover_alt(alt):
            return url
    return None


def local_asset_path(folder, number):
    path = f"assets/{folder}/issue-{number}.png"
    if os.path.isfile(path):
        return path
    return None


def cover_src_for_issue(issue, use_placeholder=True):
    body = issue.body or ""
    comment = _COVER_COMMENT_RE.search(body) if body else None
    if comment:
        return comment.group(1)
    local = local_asset_path("covers", issue.number)
    if local:
        return local
    found = extract_cover_url(body)
    if found:
        return found
    if use_placeholder:
        return PLACEHOLDER_COVER
    return None


def _cover_cell(issue):
    title = issue.title or ""
    cover = cover_src_for_issue(issue)
    date = format_time(issue.created_at)
    return (
        '    <td align="center" width="25%" valign="top">\n'
        f'      <a href="{html.escape(issue.html_url, quote=True)}">\n'
        f'        <img src="{html.escape(cover, quote=True)}" width="120"'
        f' alt="{html.escape(title + "封面", quote=True)}"><br>\n'
        f"        {html.escape(title)}\n"
        "      </a><br>\n"
        f"      <sub>{html.escape(date)}</sub>\n"
        "    </td>"
    )


def render_cover_wall(issues):
    cells = [_cover_cell(issue) for issue in issues]
    rows = []
    for start in range(0, len(cells), COVER_COLUMNS):
        chunk = cells[start : start + COVER_COLUMNS]
        rows.append("  <tr>\n" + "\n".join(chunk) + "\n  </tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>\n"


def add_md_cover_wall(md_path, issues):
    shown = list(issues)[:COVER_WALL_LIMIT]
    if not shown:
        return
    with open(md_path, "a+", encoding="utf-8") as md:
        md.write("## 📚 读书笔记\n\n")
        md.write(
            "按读完或记录时间排列，一点封面就进对应笔记。封面宽 120px。还没有封面的书先用占位图。\n\n"
        )
        md.write(render_cover_wall(shown))
        md.write("\n")


def add_md_quote_cards(md_path, issues):
    chosen = []
    for issue in issues:
        path = local_asset_path("quotes", issue.number)
        if not path:
            continue
        chosen.append((issue, path))
        if len(chosen) >= QUOTE_CARD_LIMIT:
            break
    if not chosen:
        return
    cells = []
    for issue, path in chosen:
        title = html.escape(issue.title or "", quote=True)
        cells.append(
            '    <td align="center" width="25%" valign="top">\n'
            f'      <a href="{html.escape(issue.html_url, quote=True)}">\n'
            f'        <img src="{html.escape(path, quote=True)}" width="180" alt="{title}">\n'
            "      </a>\n"
            "    </td>"
        )
    with open(md_path, "a+", encoding="utf-8") as md:
        md.write("## 语录卡片\n\n")
        md.write("<table>\n  <tr>\n" + "\n".join(cells) + "\n  </tr>\n</table>\n\n")


_YEAR_LABEL_RE = re.compile(r"^(19|20)\d{2}$")
_FRONT_MATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MD_EMPHASIS_RE = re.compile(r"(\*\*|__|~~|`)")
EXCERPT_LIMIT = 140


def is_year_label(name):
    return bool(_YEAR_LABEL_RE.fullmatch(name or ""))


def plain_excerpt(body, limit=EXCERPT_LIMIT):
    if not body:
        return ""
    text = body.replace("\r\n", "\n").replace("\r", "\n")
    text = _FRONT_MATTER_RE.sub("", text)
    text = _HTML_COMMENT_RE.sub("", text)
    text = _MD_IMAGE_RE.sub("", text)
    text = _HTML_IMAGE_RE.sub("", text)
    text = _MD_LINK_RE.sub(r"\1", text)
    text = _HTML_TAG_RE.sub("", text)
    text = _MD_EMPHASIS_RE.sub("", text)
    lines = []
    for line in text.splitlines():
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
        line = re.sub(r"\s*#{1,6}\s*$", "", line)
        line = re.sub(r"^\s{0,3}>\s?", "", line)
        line = re.sub(r"^\s*[-*+]\s+", "", line)
        line = re.sub(r"^\s*\d+\.\s+", "", line)
        lines.append(line)
    text = re.sub(r"\s+", " ", " ".join(lines)).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def write_issue_list(md, issues):
    for i, issue in enumerate(issues):
        if i == ANCHOR_NUMBER:
            md.write("<details><summary>显示更多</summary>\n")
            md.write("\n")
        add_issue_info(issue, md)
    if len(issues) > ANCHOR_NUMBER:
        md.write("</details>\n")
        md.write("\n")


def write_year_spotlight(md, issue, year_name):
    title = issue.title or ""
    href = html.escape(issue.html_url, quote=True)
    title_html = f'<a href="{href}"><strong>{html.escape(title)}</strong></a>'
    labels = [label.name for label in issue.labels if label.name != year_name]
    meta = html.escape(format_time(issue.created_at))
    if labels:
        meta += " · " + " · ".join(html.escape(name) for name in labels)
    excerpt = plain_excerpt(issue.body)
    text = f"{title_html}<br>\n      <sub>{meta}</sub>"
    if excerpt:
        text += "<br>\n      " + html.escape(excerpt)
    cover = cover_src_for_issue(issue, use_placeholder=False)
    if cover:
        alt = html.escape(title, quote=True)
        md.write("<table>\n  <tr>\n")
        md.write(
            '    <td width="96" valign="top">\n'
            f'      <a href="{href}"><img src="{html.escape(cover, quote=True)}"'
            f' width="80" alt="{alt}"></a>\n'
            "    </td>\n"
        )
        md.write(f"    <td valign=\"top\">\n      {text}\n    </td>\n")
        md.write("  </tr>\n</table>\n\n")
        return
    md.write(f"{title_html}<br>\n<sub>{meta}</sub>\n")
    if excerpt:
        md.write("\n" + html.escape(excerpt) + "\n")
    md.write("\n")


def add_md_years(repo, md_path, me):
    labels = [label for label in get_repo_labels(repo) if is_year_label(label.name)]
    labels.sort(key=lambda label: int(label.name))
    with open(md_path, "a+", encoding="utf-8") as md:
        for label in labels:
            issues = owned_issues_for_label(repo, label, me)
            if not issues:
                continue
            issues.sort(key=lambda issue: (issue.created_at, issue.number))
            md.write("## " + label.name + "\n")
            if len(issues) == 1:
                md.write("\n")
                write_year_spotlight(md, issues[0], label.name)
            else:
                write_issue_list(md, issues)


def owned_issues_for_label(repo, label, me):
    # Do not use PaginatedList.totalCount. GitHub no longer sends rel="last"
    # on these Link headers, and PyGithub then reports 0 for any list that
    # spans more than one page, which dropped the section heading.
    issues = [
        issue
        for issue in get_issues_from_label(repo, label)
        if issue and is_me(issue, me)
    ]
    issues.sort(key=lambda issue: issue.created_at, reverse=True)
    return issues


def add_md_header(md, repo_name):
    with open(md, "w", encoding="utf-8") as md:
        md.write(MD_HEAD.format(repo_name=repo_name))
        md.write("\n")


def add_md_label(repo, md, me):
    labels = get_repo_labels(repo)

    # sort lables by description info if it exists, otherwise sort by name,
    # for example, we can let the description start with a number (1#Java, 2#Docker, 3#K8s, etc.)
    labels = sorted(
        labels,
        key=lambda x: (
            x.description is None,
            x.description == "",
            x.description,
            x.name,
        ),
    )

    with open(md, "a+", encoding="utf-8") as md:
        for label in labels:
            # we don't need add top label again
            if label.name in IGNORE_LABELS or is_year_label(label.name):
                continue

            issues = owned_issues_for_label(repo, label, me)
            if not issues:
                continue

            md.write("## " + label.name + "\n")
            write_issue_list(md, issues)


def get_to_generate_issues(repo, dir_name, issue_number=None):
    md_files = os.listdir(dir_name)
    generated_issues_numbers = [
        int(i.split("_")[0]) for i in md_files if i.split("_")[0].isdigit()
    ]
    to_generate_issues = [
        i
        for i in list(repo.get_issues())
        if int(i.number) not in generated_issues_numbers
    ]
    if issue_number:
        to_generate_issues.append(repo.get_issue(int(issue_number)))
    return to_generate_issues


def generate_rss_feed(repo, filename, me):
    generator = FeedGenerator()
    generator.id(repo.html_url)
    generator.title(f"RSS feed of {repo.owner.login}'s {repo.name}")
    generator.author(
        {"name": os.getenv("GITHUB_NAME"), "email": os.getenv("GITHUB_EMAIL")}
    )
    generator.link(href=repo.html_url)
    generator.link(
        href=f"https://raw.githubusercontent.com/{repo.full_name}/master/{filename}",
        rel="self",
    )
    for issue in repo.get_issues():
        if not issue.body or not is_me(issue, me) or issue.pull_request:
            continue
        item = generator.add_entry(order="append")
        item.id(issue.html_url)
        item.link(href=issue.html_url)
        item.title(issue.title)
        item.published(issue.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
        for label in issue.labels:
            item.category({"term": label.name})
        body = "".join(c for c in issue.body if _valid_xml_char_ordinal(c))
        item.content(CDATA(marko.convert(body)), type="html")
    generator.atom_file(filename)


def main(token, repo_name, issue_number=None, dir_name=BACKUP_DIR):
    user = login(token)
    repo = get_repo(user, repo_name)
    me = get_me(repo)
    # add to readme one by one, change order here
    add_md_header("README.md", repo_name)
    for func in [add_md_firends, add_md_top, add_md_recent]:
        func(repo, "README.md", me)
    reading_notes = owned_issues_for_label(repo, READING_NOTES_LABEL, me)
    add_md_cover_wall("README.md", reading_notes)
    add_md_quote_cards("README.md", reading_notes)
    add_md_years(repo, "README.md", me)
    for func in [add_md_label, add_md_todo]:
        func(repo, "README.md", me)

    generate_rss_feed(repo, "feed.xml", me)
    to_generate_issues = get_to_generate_issues(repo, dir_name, issue_number)

    # save md files to backup folder
    for issue in to_generate_issues:
        save_issue(issue, me, dir_name)


def save_issue(issue, me, dir_name=BACKUP_DIR):
    md_name = os.path.join(
        dir_name, f"{issue.number}_{issue.title.replace('/', '-').replace(' ', '.')}.md"
    )
    with open(md_name, "w") as f:
        f.write(f"# [{issue.title}]({issue.html_url})\n\n")
        f.write(issue.body or "")
        if issue.comments:
            for c in issue.get_comments():
                if is_me(c, me):
                    f.write("\n\n---\n\n")
                    f.write(c.body or "")


if __name__ == "__main__":
    if not os.path.exists(BACKUP_DIR):
        os.mkdir(BACKUP_DIR)
    parser = argparse.ArgumentParser()
    parser.add_argument("github_token", help="github_token")
    parser.add_argument("repo_name", help="repo_name")
    parser.add_argument(
        "--issue_number", help="issue_number", default=None, required=False
    )
    options = parser.parse_args()
    main(options.github_token, options.repo_name, options.issue_number)
