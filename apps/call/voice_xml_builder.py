from dataclasses import dataclass, field
from typing import Dict, List, Optional
from django.http import HttpResponse
from xml.sax.saxutils import escape


# -------------------------
# Generic XML Node builder
# -------------------------
@dataclass
class XmlNode:
    tag: str
    attrs: Dict[str, str] = field(default_factory=dict)
    children: List["XmlNode"] = field(default_factory=list)
    text: Optional[str] = None

    def __post_init__(self):
        self.tag = self.tag.lower()

    def add(self, child: "XmlNode") -> "XmlNode":
        self.children.append(child)
        return self

    def set_attr(self, **attrs) -> "XmlNode":
        fixed = {}
        for k, v in attrs.items():
            if v is None:
                continue
            # allow python keyword-safe attrs: class_ -> class
            if k.endswith("_"):
                k = k[:-1]
            fixed[k.replace("__", ":")] = str(v)
        self.attrs.update(fixed)
        return self

    def to_xml(self, indent: int = 0) -> str:
        pad = "  " * indent
        attrs_str = "".join(f' {k}="{escape(str(v))}"' for k, v in self.attrs.items())

        if not self.children and (self.text is None or self.text == ""):
            return f"{pad}<{self.tag}{attrs_str} />"

        opening = f"{pad}<{self.tag}{attrs_str}>"
        parts = [opening]

        if self.text is not None:
            parts.append(escape(self.text))

        if self.children:
            parts.append("")
            for c in self.children:
                parts.append(c.to_xml(indent + 1))
            parts.append(f"{pad}</{self.tag}>")
        else:
            parts.append(f"</{self.tag}>")

        return "\n".join(parts)


# -------------------------
# NextGenSwitch Voice XML DSL
# -------------------------
class GetXML:
    def __init__(self):
        self._response = XmlNode("response")

    @property
    def response(self) -> "ResponseBuilder":
        return ResponseBuilder(self._response, root=self)

    def xml(self) -> str:
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + self._response.to_xml()

    def to_http_response(self) -> HttpResponse:
        return HttpResponse(self.xml(), content_type="application/xml")


class ResponseBuilder:
    def __init__(self, node: XmlNode, root: GetXML):
        self._node = node
        self._root = root

    # ---------- Flow control ----------
    def hangup(self) -> GetXML:
        self._node.add(XmlNode("Hangup"))
        return self._root

    def pause(self, length: int = 1) -> GetXML:
        self._node.add(XmlNode("Pause").set_attr(length=length))
        return self._root

    def redirect(self, url: str, method: str = "GET") -> GetXML:
        self._node.add(XmlNode("Redirect", text=url).set_attr(method=method))
        return self._root

    def bridge(self, bridge_call_id: str, bridgeAfterEstablish: Optional[bool] = None) -> GetXML:
        # docs show <Bridge bridgeAfterEstablish="true">ABC123</Bridge> :contentReference[oaicite:2]{index=2}
        val = None
        if bridgeAfterEstablish is not None:
            val = "true" if bridgeAfterEstablish else "false"
        self._node.add(XmlNode("Bridge", text=bridge_call_id).set_attr(bridgeAfterEstablish=val))
        return self._root

    def leave(self) -> GetXML:
        self._node.add(XmlNode("Leave"))
        return self._root

    # ---------- Main voice verbs ----------
    def say(self, text: str, loop: Optional[int] = None) -> GetXML:
        # docs mention loop attribute for Say :contentReference[oaicite:3]{index=3}
        self._node.add(XmlNode("Say", text=text).set_attr(loop=loop))
        return self._root

    def play(self, url_or_path: str, loop: Optional[int] = None) -> GetXML:
        # docs mention loop attribute for Play :contentReference[oaicite:4]{index=4}
        self._node.add(XmlNode("Play", text=url_or_path).set_attr(loop=loop))
        return self._root

    def record(
        self,
        action: Optional[str] = None,
        method: Optional[str] = None,
        timeout: Optional[int] = None,
        finishOnKey: Optional[str] = None,
        transcribe: Optional[bool] = None,
        trim: Optional[bool] = None,
        beep: Optional[bool] = None,
    ) -> GetXML:
        # docs list these Record attributes :contentReference[oaicite:5]{index=5}
        def b(x): return None if x is None else ("true" if x else "false")
        self._node.add(
            XmlNode("Record").set_attr(
                action=action,
                method=method,
                timeout=timeout,
                finishOnKey=finishOnKey,
                transcribe=b(transcribe),
                trim=b(trim),
                beep=b(beep),
            )
        )
        return self._root

    def gather(
        self,
        action: str,
        method: str = "POST",
        timeout: Optional[int] = None,
        speechTimeout: Optional[int] = None,
        numDigits: Optional[int] = None,
        finishOnKey: Optional[str] = None,
        actionOnEmptyResult: Optional[bool] = None,
        transcript: Optional[bool] = None,
        beep: Optional[bool] = None,
        speechProfile: Optional[str] = None,
        input: Optional[str] = None,  # "dtmf" / "speech" / "dtmf speech"
        maxDigits: Optional[int] = None,  # docs example uses maxDigits :contentReference[oaicite:6]{index=6}
    ) -> "GatherBuilder":
        # docs list Gather attributes :contentReference[oaicite:7]{index=7}
        def b(x): return None if x is None else ("true" if x else "false")
        node = XmlNode("Gather").set_attr(
            action=action,
            method=method,
            timeout=timeout,
            speechTimeout=speechTimeout,
            numDigits=numDigits,
            finishOnKey=finishOnKey,
            actionOnEmptyResult=b(actionOnEmptyResult),
            transcript=b(transcript),
            beep=b(beep),
            speechProfile=speechProfile,
            input=input,
            maxDigits=maxDigits,
        )
        self._node.add(node)
        return GatherBuilder(node, root=self._root)

    def dial(
        self,
        to: Optional[str] = None,
        action: Optional[str] = None,
        method: Optional[str] = None,
        callerId: Optional[str] = None,
        answerOnBridge: Optional[bool] = None,
        ringTone: Optional[bool] = None,
        timeLimit: Optional[int] = None,
        hangupOnStar: Optional[bool] = None,
        record: Optional[str] = None,  # record-from-answer / record-from-ringing
        recordingStatusCallback: Optional[str] = None,
        statusCallback: Optional[str] = None,
        channel: Optional[str] = None,
        channel_id: Optional[int] = None,
        body: Optional[str] = None,  # allow <Dial>1000</Dial> style
    ) -> "DialBuilder":
        # docs list Dial attributes :contentReference[oaicite:8]{index=8}
        def b(x): return None if x is None else ("true" if x else "false")
        node = XmlNode("Dial", text=body).set_attr(
            to=to,
            action=action,
            method=method,
            callerId=callerId,
            answerOnBridge=b(answerOnBridge),
            ringTone=b(ringTone),
            timeLimit=timeLimit,
            hangupOnStar=b(hangupOnStar),
            record=record,
            recordingStatusCallback=recordingStatusCallback,
            statusCallback=statusCallback,
            channel=channel,
            channel_id=channel_id,
        )
        self._node.add(node)
        return DialBuilder(node, root=self._root)

    # ---------- Stream (WebSocket) ----------
    @property
    def connect(self) -> "ConnectBuilder":
        # create/connect once
        for c in self._node.children:
            if c.tag == "connect":
                return ConnectBuilder(c, root=self._root)
        connect = XmlNode("connect")
        self._node.add(connect)
        return ConnectBuilder(connect, root=self._root)


class GatherBuilder:
    """Allows nesting <Say>/<Play> inside <Gather> then .end()"""
    def __init__(self, node: XmlNode, root: GetXML):
        self._node = node
        self._root = root

    def say(self, text: str, loop: Optional[int] = None) -> "GatherBuilder":
        self._node.add(XmlNode("Say", text=text).set_attr(loop=loop))
        return self

    def play(self, url_or_path: str, loop: Optional[int] = None) -> "GatherBuilder":
        self._node.add(XmlNode("Play", text=url_or_path).set_attr(loop=loop))
        return self

    def end(self) -> GetXML:
        return self._root


class DialBuilder:
    """Allows nesting <Play>/<Say> inside <Dial> then .end() (docs show nested Play example) :contentReference[oaicite:9]{index=9}"""
    def __init__(self, node: XmlNode, root: GetXML):
        self._node = node
        self._root = root

    def say(self, text: str, loop: Optional[int] = None) -> "DialBuilder":
        self._node.add(XmlNode("Say", text=text).set_attr(loop=loop))
        return self

    def play(self, url_or_path: str, loop: Optional[int] = None) -> "DialBuilder":
        self._node.add(XmlNode("Play", text=url_or_path).set_attr(loop=loop))
        return self

    def end(self) -> GetXML:
        return self._root


class ConnectBuilder:
    def __init__(self, node: XmlNode, root: GetXML):
        self._node = node
        self._root = root

    def stream(self, url: str, name: str = "stream", params: Optional[Dict[str, str]] = None) -> GetXML:
        # docs show <Connect><Stream ...><Parameter .../></Stream></Connect> :contentReference[oaicite:10]{index=10}
        stream = XmlNode("Stream").set_attr(name=name, url=url)
        self._node.add(stream)
        if params:
            for k, v in params.items():
                stream.add(XmlNode("Parameter").set_attr(name=k, value=v))
        return self._root
