"""Synthetic Jetstream events and API responses for the Bluesky collector tests. No real account appears here:
every DID is made up (did:plc:fake...)."""
import json

TARGET = "did:plc:faketarget0000000000000a"
TARGET2 = "did:plc:faketarget0000000000000b"
T0 = 1_795_000_000_000_000  # microseconds; 2026-11-18 11:06:40 UTC


def did(n):
    return f"did:plc:fakeuser{n:016d}"


def post_uri(author, rkey="3kfakepost222"):
    return f"at://{author}/app.bsky.feed.post/{rkey}"


def commit(author, collection, record=None, op="create", t=T0, rkey="3kfakerkey222"):
    c = {"rev": "3kfakerev2222", "operation": op, "collection": collection, "rkey": rkey}
    if op != "delete":
        c["record"] = record or {}
        c["cid"] = "bafyfake"
    return json.dumps({"did": author, "time_us": t, "kind": "commit", "commit": c})


def post(author, t=T0, reply_root=None, reply_parent=None, quote=None, text="synthetic"):
    rec = {"$type": "app.bsky.feed.post", "text": text, "createdAt": "2026-11-18T11:06:40.000Z"}
    if reply_root or reply_parent:
        rec["reply"] = {"root": {"uri": reply_root or reply_parent, "cid": "bafyfake"},
                        "parent": {"uri": reply_parent or reply_root, "cid": "bafyfake"}}
    if quote:
        rec["embed"] = {"$type": "app.bsky.embed.record", "record": {"uri": quote, "cid": "bafyfake"}}
    return commit(author, "app.bsky.feed.post", rec, t=t)


def like(author, subject_uri, t=T0, rkey="3kfakelike222"):
    return commit(author, "app.bsky.feed.like", {"subject": {"uri": subject_uri, "cid": "bafyfake"}}, t=t,
                  rkey=rkey)


def graph(author, kind, subject_did, t=T0):
    return commit(author, f"app.bsky.graph.{kind}", {"subject": subject_did}, t=t)


def delete(author, collection, t=T0, rkey="3kfakelike222"):
    return commit(author, collection, op="delete", t=t, rkey=rkey)


def identity(author, t=T0):
    return json.dumps({"did": author, "time_us": t, "kind": "identity",
                       "identity": {"did": author, "handle": "fake.example", "seq": 1}})


def label_frame(seq, labels, op=1, t="#labels"):
    """One subscribeLabels frame: two concatenated CBOR objects."""
    import cbor2
    return cbor2.dumps({"op": op, "t": t}) + cbor2.dumps({"seq": seq, "labels": labels})


def label(uri, val, cts="2026-06-15T00:00:00.000Z", neg=False, src="did:plc:fakelabeler000000000000"):
    lab = {"ver": 1, "src": src, "uri": uri, "val": val, "cts": cts, "sig": b"\x00" * 64}
    if neg:
        lab["neg"] = True
    return lab


def thread(root_author, repliers):
    """A getPostThread response with one nested reply chain per replier pair."""
    def node(author, replies=()):
        return {"post": {"uri": post_uri(author), "author": {"did": author}}, "replies": list(replies)}
    return {"thread": node(root_author, [node(a, [node(b)]) for a, b in repliers])}
