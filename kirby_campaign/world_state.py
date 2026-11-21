"""One world's records, checked together.

Structural references must resolve: who heads an organisation, who holds an
office, which polity a person belongs to, who an event's actors are, and
both parties to a relation between people, organisations or polities.

Some references may dangle, on purpose. A source can prune the long dead,
leaving their ids in kin lists and organisation member lists; those are
kept and not checked. Locale ids are not checked here either: locales live
in kirby-world's ``Atlas``, and a consumer that holds both checks them
together. A WorldState never needs an Atlas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kirby_campaign.organisation import Organisation, Relation
from kirby_campaign.person import Person
from kirby_campaign.polity import Office, Polity, Tenure
from kirby_campaign.timeline import Law, WorldEvent

#: The collections a WorldState holds, and the singular name used in errors.
_KINDS = (
    ("polities", "polity"),
    ("offices", "office"),
    ("tenures", "tenure"),
    ("people", "person"),
    ("organisations", "organisation"),
    ("relations", "relation"),
    ("events", "event"),
    ("laws", "law"),
)


@dataclass(frozen=True, kw_only=True)
class WorldState:
    world_id: str
    polities: tuple[Polity, ...]
    offices: tuple[Office, ...]
    tenures: tuple[Tenure, ...]
    people: tuple[Person, ...]
    organisations: tuple[Organisation, ...]
    relations: tuple[Relation, ...]
    events: tuple[WorldEvent, ...]
    laws: tuple[Law, ...]

    def __post_init__(self) -> None:
        index: dict[str, dict[str, Any]] = {}
        for collection, kind in _KINDS:
            by_id: dict[str, Any] = {}
            for record in getattr(self, collection):
                if record.world_id != self.world_id:
                    raise ValueError(
                        f"{kind} {record.id!r} belongs to world {record.world_id!r}, "
                        f"not {self.world_id!r}"
                    )
                if record.id in by_id:
                    raise ValueError(f"{kind} id {record.id!r} is used twice")
                by_id[record.id] = record
            index[kind] = by_id
        shared = index["person"].keys() & index["organisation"].keys()
        if shared:
            raise ValueError(
                f"ids used by both a person and an organisation: {', '.join(sorted(shared))}"
            )
        object.__setattr__(self, "_index", index)
        self._check_source_identity()
        self._check_references()

    def _check_source_identity(self) -> None:
        """Sync matches records by SourceRef, so a SourceRef names one record
        in this world and nowhere else."""
        owners: dict[object, str] = {}
        for collection, kind in _KINDS:
            for record in getattr(self, collection):
                refs = getattr(record, "source_refs", None)
                if refs is None:
                    single = getattr(record, "source_ref", None)
                    refs = () if single is None else (single,)
                for ref in refs:
                    owner = f"{kind} {record.id!r}"
                    if ref.world_id != self.world_id:
                        raise ValueError(
                            f"{owner}: source ref {ref} names world {ref.world_id!r}, "
                            f"not {self.world_id!r}"
                        )
                    if ref in owners:
                        raise ValueError(f"source ref {ref} is claimed by {owners[ref]} and {owner}")
                    owners[ref] = owner

    def _must_exist(self, kind: str, record_id: str, owner: str, field: str) -> None:
        if record_id not in self._index[kind]:
            raise ValueError(f"{owner}: {field} names {kind} {record_id!r}, which is not in the world")

    def _check_references(self) -> None:
        for p in self.people:
            if p.polity_id is not None:
                self._must_exist("polity", p.polity_id, f"person {p.id!r}", "polity_id")
        for o in self.organisations:
            for role in ("head_id", "heir_id"):
                if getattr(o, role) is not None:
                    self._must_exist("person", getattr(o, role), f"organisation {o.id!r}", role)
        for office in self.offices:
            owner = f"office {office.id!r}"
            self._must_exist("polity", office.polity_id, owner, "polity_id")
            if office.scope_kind in ("polity", "organisation"):
                self._must_exist(office.scope_kind, office.scope_id, owner, "scope_id")
        for t in self.tenures:
            self._must_exist("office", t.office_id, f"tenure {t.id!r}", "office_id")
            self._must_exist("person", t.person_id, f"tenure {t.id!r}", "person_id")
        for r in self.relations:
            for side in ("a", "b"):
                ref = getattr(r, side)
                if ref.kind != "locale":
                    self._must_exist(ref.kind, ref.id, f"relation {r.id!r}", side)
        for law in self.laws:
            self._must_exist("polity", law.polity_id, f"law {law.id!r}", "polity_id")
        for e in self.events:
            for actor in e.actors:
                self._must_exist("person", actor, f"event {e.id!r}", "actors")

    def _get(self, kind: str, record_id: str) -> Any:
        try:
            return self._index[kind][record_id]
        except KeyError:
            raise KeyError(f"the world has no {kind} {record_id!r}") from None

    def person(self, person_id: str) -> Person:
        return self._get("person", person_id)

    def has_person(self, person_id: str) -> bool:
        return person_id in self._index["person"]

    def organisation(self, organisation_id: str) -> Organisation:
        return self._get("organisation", organisation_id)

    def polity(self, polity_id: str) -> Polity:
        return self._get("polity", polity_id)

    def office(self, office_id: str) -> Office:
        return self._get("office", office_id)

    def relation(self, relation_id: str) -> Relation:
        return self._get("relation", relation_id)

    def event(self, event_id: str) -> WorldEvent:
        return self._get("event", event_id)

    def holders_of(self, office_id: str) -> tuple[Person, ...]:
        """Who holds ``office_id`` now (an open tenure)."""
        self.office(office_id)
        return tuple(self.person(t.person_id) for t in self.tenures
                     if t.office_id == office_id and t.is_open)

    def offices_held_by(self, person_id: str) -> tuple[Office, ...]:
        return tuple(self.office(t.office_id) for t in self.tenures
                     if t.person_id == person_id and t.is_open)
