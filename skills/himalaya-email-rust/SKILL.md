---
name: himalaya-email-rust
description: |
  Manage email from the terminal using Himalaya v2. Supports IMAP, SMTP, JMAP, Gmail REST API, Microsoft Graph, Maildir, m2dir, JSON automation, and email attachments.

  Triggers when user mentions:
  - "check", "read" or "list" emails
  - "send", "reply", "forward", "delete", "move", or "copy" emails
  - downloading or sending email attachments
author: Jansen Lin
license: MIT
allowed-tools: Bash,Read,Write
---

# Himalaya Email Manager

Manage email with Himalaya v2.0.0+. Primary: built-in v2 commands. For simple email attachments, use `message compose --attach`. For rich MIME, signing, encryption, or custom formatting, generate a valid `.eml` file and pass it to `message send`.

All commands are stateless. Check the installed binary's `--help` when a command or flag is version-sensitive.

## Decision

1. Check the binary and account first: `himalaya --version` and `himalaya account check --json`.
2. For a normal text email or ordinary attachment, use **Path A (`message compose`)**.
3. For multipart MIME or custom headers, use **Path B (`message send` with `.eml`)**.
4. For Gmail SMTP, do not pass `--save sent` unless a duplicate Sent copy is explicitly requested. Gmail normally saves sent messages automatically.
5. For machine processing, use `--json` and keep the mailbox together with every message id.

## Environment Check

```bash
command -v himalaya
himalaya --version
himalaya account list --json
himalaya account check --json
```

If Himalaya is not in PATH, check the common Cargo location:

```bash
test -x "$HOME/.cargo/bin/himalaya" && "$HOME/.cargo/bin/himalaya" --version
```

Install a stable release using the official release assets or installer. OAuth and secret storage are provided through external tools such as password managers and token brokers.

Official references:

- [Himalaya README](https://github.com/pimalaya/himalaya/blob/v2.0.0/README.md)
- [Himalaya releases](https://github.com/pimalaya/himalaya/releases)

## Safety

- Never print, log, or include passwords, app passwords, OAuth tokens, or `.env` contents.
- Verify the recipient, subject, body, and attachment paths before sending.
- Do not use `--save sent` for Gmail SMTP unless a manual Sent copy is required.
- Use `--log-level off` when clean JSON output is required.

## Configuration

Config files are loaded from the first valid path among:
- `$XDG_CONFIG_HOME/himalaya/config.toml`
- `$HOME/.config/himalaya/config.toml`
- `$HOME/.himalayarc`

Inspect accounts and connectivity:

```bash
himalaya account list --json
himalaya account check --account "Account Name" --json
```

Run bare `himalaya` for the account discovery wizard.

### IMAP and SMTP

```toml
[accounts.gmail]
default = true

imap.server = "imaps://imap.gmail.com:993"
imap.sasl.plain.username = "user@example.com"
imap.sasl.plain.password.command = ["pass", "show", "gmail"]

smtp.server = "smtps://smtp.gmail.com:465"
smtp.sasl.plain.username = "user@example.com"
smtp.sasl.plain.password.command = ["pass", "show", "gmail"]

mailbox.alias.inbox = "INBOX"
mailbox.alias.sent = "[Gmail]/Sent Mail"
mailbox.alias.drafts = "[Gmail]/Drafts"
mailbox.alias.trash = "[Gmail]/Trash"
```

Himalaya does not automatically load `.env` files. Source one explicitly from the password command:

```toml
imap.sasl.plain.password.command = ["sh", "-c", ". /path/to/.env; printf '%s' \"$GMAIL_APP_PASSWORD\""]
smtp.sasl.plain.password.command = ["sh", "-c", ". /path/to/.env; printf '%s' \"$GMAIL_APP_PASSWORD\""]
```

Keep config and secret files private:

```bash
chmod 600 ~/.config/himalaya/config.toml ~/.config/himalaya/.env
```

For Gmail REST API, use an OAuth 2.0 bearer token from a broker such as `ortie`:

```toml
gmail.auth.token.command = ["ortie", "token", "show", "-a", "gmail"]
```

Select it with `-b gmail` when the account has multiple backends. App passwords work with the IMAP/SMTP configuration, not the Gmail REST backend.

## File Handling

Let the caller choose attachment paths. Do not hardcode a machine-specific source path.

When a temporary `.eml` is needed, use the task's working directory or the workspace `Workbench/` directory. Remove temporary MIME files after successful delivery unless the user asks to retain them.

## Path A: Compose and Send

### Plain Email

```bash
himalaya message compose \
  --from sender@example.com \
  --to recipient@example.com \
  --subject "Subject" \
  --body "Email body" \
  --send
```

### Email with Attachment

```bash
himalaya message compose \
  --from sender@example.com \
  --to recipient@example.com \
  --subject "Document" \
  --body "Please see the attached document." \
  --attach /path/to/document.pdf \
  --send
```

Repeat `--attach` for multiple files. Use `--save sent` only when a manual Sent copy is required.

### Reply and Forward

```bash
himalaya message reply -m inbox 42 --body "Reply text" --send
himalaya message forward -m inbox 42 --to recipient@example.com --send
```

Both support `--attach`, `--body-file`, `--cc`, `--bcc`, `--save`, and `--send`.

## Path B: Raw MIME

Use this path for rich MIME, custom headers, signing, encryption, or a message generated by Python's `EmailMessage`.

Send a prepared message:

```bash
himalaya message send --account "Account Name" message.eml
```

Or pipe a MIME message through stdin:

```bash
cat message.eml | himalaya message send --account "Account Name"
```

`message send` accepts a file path, inline raw message, or stdin. Do not manually put base64 data into shell arguments.

## Read and Search

### Mailboxes

```bash
himalaya mailbox list --json
```

Use aliases from `[mailbox.alias]`, such as `inbox`, `sent`, `drafts`, and `trash`.

### Envelopes

```bash
himalaya envelope list -m inbox --json
himalaya envelope list -m sent --recipient --has-attachment --json
himalaya envelope list -m inbox --page 1 --page-size 20 --json
```

`--has-attachment` populates the attachment column; it does not filter messages by itself.

### Search

```bash
himalaya envelope search -m inbox "from alice@example.com and after 2026-05-01" --json
himalaya envelope search -m inbox "subject invoice order by date desc" --json
himalaya envelope search -m inbox "not flag seen" --json
```

Supported conditions include `date`, `after`, `from`, `to`, `subject`, `body`, and `flag`. Combine conditions with `and`, `or`, `not`, and parentheses.

### Read Messages

```bash
# Render headers and text bodies
himalaya message read -m inbox 42

# Parsed JSON
himalaya message read -m inbox 42 --json

# Raw RFC 5322 bytes
himalaya message read -m inbox 42 --raw > message.eml
```

## Message Management

### Copy and Move

```bash
himalaya message copy -f inbox -t archive 42
himalaya message move -f inbox -t archive 42
```

### Flags

```bash
himalaya flag add -m inbox --flag seen 42
himalaya flag add -m inbox --flag flagged 42
himalaya flag set -m inbox --flag seen 42
himalaya flag remove -m inbox --flag seen 42
```

## Attachments

List attachments before downloading:

```bash
himalaya attachment list -m inbox 42 --json
```

Download all attachments:

```bash
himalaya attachment download -m inbox 42 --dir /desired/target/folder
```

Download selected attachment ids:

```bash
himalaya attachment download -m inbox 42 1 2 --dir /desired/target/folder
```

Attachment ids are the 1-based ids returned by `attachment list`. If `--dir` is omitted, the account/global `downloads-dir` setting is used.

## JSON Automation

Common v2 envelope fields:

```json
{
  "id": "42",
  "message-id": "<message@example.com>",
  "subject": "Example",
  "from": [{"name": "Sender", "email": "sender@example.com"}],
  "to": [{"name": null, "email": "recipient@example.com"}],
  "date": "2026-08-17T10:00:00+10:00",
  "has-attachment": true
}
```

`from` and `to` are arrays. Address values use `email`. Attachment status uses `has-attachment`. Message ids are backend-specific, so retain the mailbox used to obtain each id.

```python
for envelope in data.get("envelopes", data):
    senders = envelope.get("from", [])
    addresses = [item.get("email", "") for item in senders]
    if envelope.get("has-attachment"):
        print(envelope.get("id"), addresses)
```

## Output Verification

After sending an attachment, verify it when delivery correctness matters:

```bash
himalaya attachment list -m sent MESSAGE_ID --json
```

For Gmail SMTP, do not add `--save sent` during this verification workflow unless a second Sent copy is intentional.

## Common Issues

| Error or symptom | Solution |
|---|---|
| `command not found: himalaya` | Check PATH and `$HOME/.cargo/bin/himalaya`; install a stable release. |
| `account check` authentication failure | Verify the app password, username, endpoint, and password command output. |
| Gmail `Folder doesn't exist` | Configure `mailbox.alias.sent = "[Gmail]/Sent Mail"`, or omit `--save` for SMTP. |
| Duplicate Sent records | Gmail already saves SMTP messages; omit `--save sent`. |
| Attachment missing | Use `message compose --attach` or verify the MIME message has a valid attachment part. |
| Need original MIME | Use `message read --raw`. |
| Need custom multipart MIME | Generate `.eml` and use `message send`. |
| JSON contains unexpected fields | Run the installed command with `--help` and inspect the current `--json` output. |

## Provider Notes

| Provider | v2 backend | Typical auth |
|---|---|---|
| Gmail | IMAP/SMTP or native `gmail` REST | App Password or OAuth 2.0 |
| Outlook/Microsoft 365 | IMAP/SMTP or `msgraph` | OAuth 2.0 |
| Fastmail | IMAP/SMTP or JMAP | App Password or API token |
| Proton Mail | IMAP/SMTP through Proton Bridge | Bridge password |
| iCloud Mail | IMAP/SMTP | App-specific password |
