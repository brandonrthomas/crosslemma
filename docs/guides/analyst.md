# An analyst

This guide helps you, the user, set up and work with an analyst session beside an instance, if you want one: what it
is for, how to start it from the templates, how its text reaches the instance, and where it stops.

An analyst is **optional**. The kit has no analyst role, and nothing in the method depends on one
([FLOW.md, an analyst](../../FLOW.md#an-analyst-and-the-operator-agent); [RULES.md §12](../../RULES.md#12-dropped--and-why)).
It is a standing conversation you keep at your own discretion, for design questions, second readings and "what did this
miss?". For the roles that are part of the method, see [roles](../concepts/roles.md).

## Where it stands

**Outside the trust chain.** An analyst is never a step in the cycle, a gate, or a source of claims, even when you
designate it the operator agent ([RULES.md](../../RULES.md#rules), "Words"): it then gives direction within the operator's
list in [RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc), and everything on your list stays yours. Anything it produces
is uncertified until it has been checked against the record point by point, and it reaches the record only the way
anything else does: through a run, a claim and a referee ([the trust model](../concepts/trust-model.md);
→ **The user's analyst's notes are uncertified**).

**Its text is outside input.** Whatever the analyst writes for the instance, including text you relay as your own, gets an
intake record in `intake/` before anything acts on it. Your own explicit requests in such a text are yours; its factual
claims are checked like any outside input
([RULES.md, outside input](../../RULES.md#outside-input); → **Outside input has an intake record first**). See
[packets and outside input](../concepts/packets-and-outside-input.md) for what that does to a packet.

## 1. Give it a directory of its own

The analyst works in a directory outside the instance, which holds its own handoff and a `notes/` folder. It never writes in
the instance. A session opened in that directory is not covered by the instance's hook: the hook is registered in the
instance's own settings and acts only in sessions opened there. So what keeps an analyst away from the instance's tools is
its prompt, which is a rule, not a gate. The analyst prompt has the analyst check, at every start, whether a user-level
hook refusing any session's command that names the approval tool is registered in your user settings, and say so if not.
Such a hook must let through the one plain call from a session opened in an instance, which that instance's hook turns
into your tap ([Approving](approving.md#2b-approve-with-a-tap)); a hook without that exception would close the tap route.
The kit does not ship such a hook.

## 2. Start it from the template

Copy `templates/analyst-prompt.md` into the analyst's directory and fill every `⟨slot⟩`: the instance's path
(`⟨INSTANCE⟩`), the problem's slug, and the analyst's own directory (`⟨ANALYST_DIR⟩`). Delete what the instance does not
have. Paste the text after the first horizontal rule (`---`) as the session's opening prompt. The template is a form, not a rule: `RULES.md`,
`FLOW.md` and the instance's `HANDOFF.md` win where they say more.

What the prompt sets up, in short:

- **Start of session.** The analyst reads its own handoff and newest notes, then the instance's handoff and `CLAIMS.md` from
  the last entry it knows, checks what is in flight (`systemctl --user list-units 'kit-run-*' 'kit-queue-*'`), tells you
  what it understands and what is pending on you, and waits.
- **Hard rules.** It writes only in its own directory. It reads the instance freely but never `data/locked/`, never the
  ledger's contents, never a run in flight, never a credential. It never runs the instance's tools; it reads their source.
- **Approvals never pass through it.** It learns of an approval only as a digest and a description. You approve at your
  terminal or by the tap in the orchestrator's session ([Approving](approving.md)); neither route passes through the
  analyst, and it never prints, relays or stores an approval command.
- **Trust tiers.** It labels everything it says: the instance's ledger as earned (quoted), its own computation (at most
  "verified computation", never "proved"), and other models' output (an opinion).
- **Audits.** Before calling anything "fine", it checks what can be checked, read-only, and says what it checked:
  manifests against their sources, statements against the ledger verbatim, referee files read directly, sentences against
  what scripts assert, mutations, dependencies, model families.
- **Records.** A timestamped running log in `notes/`, and a handoff with a state block, its standing permissions in your
  words, and its own errors.

## 3. Moving its text into the instance

You carry the analyst's text to the orchestrator; it does not go there by itself.

- The analyst gives you a short fenced block marked **[Analyst-drafted, relayed by the user.]**: rulings and meaning,
  never packet text, never an approval command, never a report of an act at your terminal as done.
- You paste it into the orchestrator's session. The orchestrator writes an intake record
  (`templates/intake-record.md`) before acting on it, and you rule the class of each item: target statement, premise,
  framing, data, tool, or record-only. Until you rule, it is record-only
  ([RULES.md, outside input](../../RULES.md#outside-input)).
- **Text bound for a packet** (a problem statement, a brief, a ledger note): the analyst gives the meaning and the
  orchestrator writes the words. A new instance blocks `intake/` from every packet, and the packet scan refuses a packet
  that shares a run of twelve words with blocked material that no open material excuses, so a packet carrying the
  analyst's own words would be refused (→ **No packet carries blocked material**).
- **Independence.** The intake record names the author family, here the analyst's model family; its "seen by" lists every
  run, model family and session the text later reaches. When referees are chosen,
  the family of each outside input a claim rests on counts, as well as the producer's
  ([RULES.md, outside input](../../RULES.md#outside-input), rule 7).

## 4. The orchestrator's side

`templates/orchestrator-prompt.md` is the matching session prompt for an instance's orchestrator: start of session,
session purposes, the approval gate, runs, claims, outside input, records. Use it to write the opening prompt in the
instance's handoff, or beside it; the handoff's own opening prompt is required in every handoff and wins where they differ.
Its section on outside input is what the orchestrator does with anything the analyst sends.

## 5. Deciding

The analyst advises; you decide. Method and tool changes, interpretations of the rules, scope and session purpose,
independence and security questions, and any disagreement between the analyst and the orchestrator are yours. The prompt
asks the analyst to put them to you in its own pane with a recommendation and the cost of each option.

## The bus channel: an appendix, your choice

Both prompt templates end with an appendix for a direct channel between the analyst and the orchestrator over Clatter,
a message bus between Claude Code sessions. Opening and closing it is yours ([RULES.md §4](../../RULES.md#4-roles--three-plus-ad-hoc),
item 8): the analyst never becomes a step or a gate, and a bus is not the control path for approvals. P7, the charter
for an unattended operator agent, is not built. If you turn it on, each appendix
lists the minimum conditions, from its side. Among them:

- you turn it on per session, by name, and can hold or end it at any time;
- approvals never travel over it as runnable text, and nothing that arrives over it is an approval;
- taps only behind a relay that cannot answer a permission prompt;
- every message the orchestrator receives is outside input, with an intake record;
- while it is on, the orchestrator tells the analyst everything it tells you, unasked, one message per step (not per
  action), and ends every message with what is pending on you and what is uncommitted; the analyst writes only when it
  would change a decision, and neither side confirms receipt.

The instance's hook keeps the orchestrator to Clatter's dispatcher: no keys typed into another pane, no mailbox touched
directly, no sender flags ([RULES.md §9](../../RULES.md#9-the-sandbox--enforced-not-convention);
→ **An orchestrator types into no other pane and touches no mailbox**). Read the appendices themselves before turning the
channel on.

## Related

- [Roles](../concepts/roles.md): user, orchestrator, worker, referee, and where an analyst is not.
- [Packets and outside input](../concepts/packets-and-outside-input.md): the intake record and the packet scan.
- [Templates](../../templates/README.md): every form, with who fills it.
