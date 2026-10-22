"""robots.txt rules per RFC 9309, including the ``*`` and ``$`` wildcards.

The standard library's ``urllib.robotparser`` matches rules as plain prefixes, so a rule such
as ``Disallow: *.html`` never matches and the page would be fetched. Directory sites use
wildcard rules heavily, so the crawler uses this matcher instead.
"""

import re
import urllib.parse
from dataclasses import dataclass, field

from apps.collector.constants import ROBOTS_ALLOW, ROBOTS_DISALLOW, ROBOTS_USER_AGENT


@dataclass(frozen=True)
class _Rule:
    """One allow/disallow line, compiled."""

    allow: bool
    pattern: str
    regex: re.Pattern[str] = field(compare=False)


def _compile(pattern: str) -> re.Pattern[str]:
    """Turn a robots path pattern into an anchored regex (``*`` any run, ``$`` end)."""
    ends_here = pattern.endswith("$")
    body = pattern[:-1] if ends_here else pattern
    regex = ".*".join(re.escape(part) for part in body.split("*"))
    return re.compile(regex + ("$" if ends_here else ""))


def _product_token(user_agent: str) -> str:
    """The User-Agent's product token: ``GovAssist-research/1.0 (…)`` → ``govassist-research``."""
    return user_agent.split("/", 1)[0].split(" ", 1)[0].strip().lower()


class RobotsRules:
    """The rules of one robots.txt for one crawler.

    Group choice: the groups naming our product token, else the ``*`` groups. Rule choice:
    the longest matching pattern wins; on a tie, allow wins (RFC 9309 §2.2.2).
    """

    def __init__(self, text: str, user_agent: str) -> None:
        self._rules = self._select(text, _product_token(user_agent))

    @staticmethod
    def _groups(text: str) -> list[tuple[set[str], list[_Rule]]]:
        """Parse the file into (agents, rules) groups; consecutive agent lines share a group."""
        groups: list[tuple[set[str], list[_Rule]]] = []
        in_rules = True
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, value = (part.strip() for part in line.split(":", 1))
            key = key.lower()
            if key == ROBOTS_USER_AGENT:
                if in_rules:
                    groups.append((set(), []))
                    in_rules = False
                groups[-1][0].add(value.lower())
            elif key in (ROBOTS_ALLOW, ROBOTS_DISALLOW) and groups:
                in_rules = True
                if value:  # an empty Disallow allows everything
                    groups[-1][1].append(_Rule(key == ROBOTS_ALLOW, value, _compile(value)))
        return groups

    def _select(self, text: str, token: str) -> list[_Rule]:
        """Rules of the groups for ``token``, or of the ``*`` groups."""
        groups = self._groups(text)
        mine = [rules for agents, rules in groups if token in agents]
        chosen = mine or [rules for agents, rules in groups if "*" in agents]
        return [rule for rules in chosen for rule in rules]

    def allowed(self, url: str) -> bool:
        """True when ``url`` (path + query) may be fetched.

        Args:
            url: An absolute URL.
        """
        parts = urllib.parse.urlsplit(url)
        target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        matches = [rule for rule in self._rules if rule.regex.match(target)]
        if not matches:
            return True
        best = max(matches, key=lambda rule: (len(rule.pattern), rule.allow))
        return best.allow
