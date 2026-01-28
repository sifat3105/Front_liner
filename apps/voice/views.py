from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import Agent
from .serializers import AgentSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse


# OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_API_KEY = "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"
REALTIME_SESSION_URL = "https://api.openai.com/v1/realtime/sessions"
CHAT_URL = "https://api.openai.com/v1/chat/completions"


# -------- Owner-scoped CRUD --------
class AgentsListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Agent.objects.filter(owner=request.user).order_by("-updated_at")
        return Response(AgentSerializer(qs, many=True).data, status=200)

    def post(self, request):
        ser = AgentSerializer(data=request.data)
        if ser.is_valid():
            ser.save(owner=request.user)
            return Response(ser.data, status=201)
        return Response(ser.errors, status=400)


class AgentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(Agent, pk=pk, owner=request.user)

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        return Response(AgentSerializer(obj).data, status=200)

    def put(self, request, pk):
        obj = self.get_object(request, pk)
        ser = AgentSerializer(obj, data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=200)
        return Response(ser.errors, status=400)

    def patch(self, request, pk):
        obj = self.get_object(request, pk)
        ser = AgentSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=200)
        return Response(ser.errors, status=400)

    def delete(self, request, pk):
        obj = self.get_object(request, pk)
        obj.delete()
        return Response(status=204)



        



# views.py
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import requests
from .models import Agent

# assume these are defined in settings or module scope:
# OPENAI_API_KEY, REALTIME_SESSION_URL

@method_decorator(csrf_exempt, name='dispatch')
class PublicVoiceStartView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, public_id):
        # fetch agent and ensure enabled
        agent = get_object_or_404(Agent, public_id=public_id, enabled=True)

        if not OPENAI_API_KEY:
            return Response({"error": "OPENAI_API_KEY missing"}, status=500)

        # Decide which text to send as system/instructions for the session
        # Prefer welcome_message, fallback to agent_prompt
        initial_instructions = (agent.welcome_message or "").strip() or (agent.agent_prompt or "").strip()

        payload = {
            "model": "gpt-realtime",
            # send agent_prompt as system instructions for the session,
            # but we will also return initial_instructions separately for the embed JS to send
            "instructions": agent.agent_prompt or ""
        }

        try:
            r = requests.post(
                REALTIME_SESSION_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=20
            )
        except requests.RequestException as e:
            return Response({"error": f"Upstream request failed: {e}"}, status=502)

        if r.status_code >= 400:
            return Response({
                "error": "Upstream error creating realtime session",
                "status": r.status_code,
                "body": r.text
            }, status=r.status_code)

        data = r.json()
        ek = (data.get("client_secret") or {}).get("value") or data.get("value")
        exp = (data.get("client_secret") or {}).get("expires_at")
        if not ek:
            return Response({"error": "No ek in upstream response", "upstream": data}, status=502)

        # Return ek plus initial_instructions for the embed JS to use
        return Response({
            "value": ek,
            "expires_at": exp,
            "sdp_url": "https://api.openai.com/v1/realtime?model=gpt-realtime",
            "headers": {"OpenAI-Beta": "realtime=v1"},
            "initial_instructions": initial_instructions,
            "voice": agent.voice or "alloy"
        }, status=200)








# -------- Public: Chat (by public_id) --------
@method_decorator(csrf_exempt, name='dispatch')
class PublicChatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, public_id):
        agent = get_object_or_404(Agent, public_id=public_id, enabled=True)
        user_msg = (request.data or {}).get("message", "")

        system = agent.agent_prompt or "You are a helpful Bengali assistant."
        business_blob = f"Business details (JSON): {agent.business_details}"

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system},
                {"role": "system", "content": business_blob},
                {"role": "user", "content": user_msg},
            ],
        }

        try:
            r = requests.post(
                CHAT_URL,
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json=payload, timeout=30
            )
        except requests.RequestException as e:
            return Response({"error": f"Upstream request failed: {e}"}, status=502)

        if r.status_code >= 400:
            return Response({"error": r.text}, status=r.status_code)

        data = r.json()
        reply = data["choices"][0]["message"]["content"]
        return Response({"reply": reply}, status=200)



# -------- Owner: Get Embed code (copy/paste) --------

class AgentEmbedInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # ensure owner matches
        agent = get_object_or_404(Agent, pk=pk, owner=request.user)

        # Only return embed code if the agent is enabled
        if not agent.enabled:
            return Response(
                {"detail": "Embed code not available. This agent is not enabled by admin."},
                status=status.HTTP_403_FORBIDDEN
            )

        embed_js_url = request.build_absolute_uri(reverse("voice-embed-js-v2"))
        base_url = f"{request.scheme}://{request.get_host()}"
        code = (f'<script defer src="{embed_js_url}" '
                f'data-agent="{agent.public_id}" data-base-url="{base_url}"></script>')
        return Response({"public_id": str(agent.public_id), "embed_code": code}, status=status.HTTP_200_OK)







# def embed_js_v2(request):
#     """
#     Public loader JS that adds a floating mic button + a minimal chat panel.
#     - Voice: POST /api/embed/agents/<public_id>/voice/start/   (simple request: no headers/body)
#     - Chat : POST /api/embed/agents/<public_id>/chat/          (form-encoded; no custom header)
#     Notes:
#       * We intentionally avoid custom headers to skip CORS preflight (OPTIONS).
#       * BASE is normalized to avoid double slashes.
#       * Right-click (contextmenu) on mic button toggles the chat panel.
#     """
#     js = r"""
# (function(){
#   'use strict';

#   // --- Resolve script tag, public_id, base URL ---
#   var s = document.currentScript || (function(){var t=document.getElementsByTagName('script');return t[t.length-1];})();
#   var PUBLIC_ID = (s.getAttribute('data-agent') || '').trim();
#   var BASE = (s.getAttribute('data-base-url') || (new URL(s.src)).origin || '').trim();
#   BASE = BASE.replace(/\/+$/,''); // remove trailing slashes

#   if(!PUBLIC_ID){
#     console.warn('[voice-embed] Missing data-agent (public_id).');
#     return;
#   }

#   // --- Inject styles ---
#   var st = document.createElement('style');
#   st.textContent = `
#     .va-floating{position:fixed;right:20px;bottom:20px;z-index:2147483647;}
#     .va-btn{width:56px;height:56px;border-radius:50%;border:0;background:#16a34a;color:#06130a;font-size:22px;cursor:pointer;box-shadow:0 8px 25px rgba(0,0,0,.25)}
#     .va-btn.stop{background:#ef4444;color:#190b0b}
#     .va-badge{position:fixed;right:90px;bottom:30px;background:rgba(0,0,0,.75);color:#fff;padding:6px 10px;border-radius:10px;font:13px system-ui;z-index:2147483647;display:none}
#     .va-panel{position:fixed;right:20px;bottom:86px;width:320px;max-height:50vh;overflow:auto;background:#0b1220;color:#e5e7eb;border:1px solid #1f2937;border-radius:12px;padding:10px;box-shadow:0 8px 30px rgba(0,0,0,.3);display:none}
#     .va-row{display:flex;gap:6px;margin-top:8px}
#     .va-input{flex:1;background:#0f172a;border:1px solid #1f2937;border-radius:10px;color:#e5e7eb;padding:8px 10px}
#     .va-send{border:0;border-radius:10px;background:#38bdf8;color:#002f47;padding:8px 10px;cursor:pointer}
#     .va-chat{display:flex;flex-direction:column;gap:6px}
#     .va-bubble{max-width:85%;padding:8px 10px;border-radius:10px;border:1px solid #1f2937;white-space:pre-wrap}
#     .va-user{align-self:flex-end;background:#0f172a}
#     .va-bot{align-self:flex-start;background:#0b1324}
#   `;
#   document.head.appendChild(st);

#   // --- Build UI ---
#   var wrap = document.createElement('div'); wrap.className='va-floating';
#   var btn  = document.createElement('button'); btn.className='va-btn'; btn.textContent='🎙️'; btn.title='Start Voice';
#   var badge = document.createElement('div'); badge.className='va-badge'; badge.textContent='Connecting...';
#   var panel = document.createElement('div'); panel.className='va-panel';
#   panel.innerHTML = '<div class="va-chat" id="va_chat"></div>'
#                   + '<div class="va-row"><input id="va_msg" class="va-input" placeholder="Write a message...">'
#                   + '<button id="va_send" class="va-send">Send</button></div>';
#   wrap.appendChild(btn);
#   document.body.appendChild(wrap);
#   document.body.appendChild(badge);
#   document.body.appendChild(panel);

#   // --- Refs & state ---
#   var chatDiv = panel.querySelector('#va_chat');
#   var inp     = panel.querySelector('#va_msg');
#   var sendBtn = panel.querySelector('#va_send');

#   var audio = null, pc=null, dc=null, mic=null, inCall=false;

#   function showBadge(t){ badge.textContent=t; badge.style.display='block'; }
#   function hideBadge(){ badge.style.display='none'; }
#   function bubble(text, who){
#     var d=document.createElement('div'); d.className='va-bubble '+who; d.textContent=text;
#     chatDiv.appendChild(d); chatDiv.scrollTop=chatDiv.scrollHeight;
#   }
#   function togglePanel(){ panel.style.display = (panel.style.display==='block'?'none':'block'); }

#   // --- Chat (preflight-free: form-encoded, no custom headers) ---
#   async function sendChat(){
#     var t=inp.value.trim(); if(!t) return; inp.value=''; bubble(t,'va-user');
#     try{
#       var body = new URLSearchParams({ message: t });
#       var r = await fetch(BASE + '/api/embed/agents/' + PUBLIC_ID + '/chat/', {
#         method: 'POST',
#         body  : body
#         // No custom headers → browser sets application/x-www-form-urlencoded; avoids preflight
#       });
#       var j = await r.json();
#       if(!r.ok) throw new Error(j && j.error || ('status ' + r.status));
#       bubble(j.reply || JSON.stringify(j), 'va-bot');
#     }catch(err){
#       bubble('⚠️ ' + (err && err.message || err), 'va-bot');
#     }
#   }

#   sendBtn.addEventListener('click', sendChat);
#   inp.addEventListener('keydown', function(e){ if(e.key==='Enter') sendChat(); });

#   // Right-click on mic button toggles chat panel
#   btn.addEventListener('contextmenu', function(e){ e.preventDefault(); togglePanel(); });

#   // --- Voice (WebRTC) ---
#   async function start(){
#     btn.disabled = true;
#     showBadge('Requesting mic + session...');

#     try{
#       // 1) Get ephemeral token (simple request: no headers/body → no preflight)
#       var tr = await fetch(BASE + '/api/embed/agents/' + PUBLIC_ID + '/voice/start/', { method:'POST' });
#       var tj = await tr.json();
#       if(!tr.ok) throw new Error(tj && tj.error || ('status ' + tr.status));

#       var ek = tj.value;
#       var sdpURL = tj.sdp_url || 'https://api.openai.com/v1/realtime?model=gpt-realtime';
#       var extraHdr = tj.headers || {};
#       if(!ek) throw new Error('No ek received');

#       // 2) Create RTCPeerConnection
#       pc = new RTCPeerConnection();

#       // Optional data channel for realtime events
#       dc = pc.createDataChannel('oai-events');
#       dc.onopen = function(){
#         showBadge('Say something!'); setTimeout(hideBadge, 1200);
#         try{
#           dc.send(JSON.stringify({
#             type: "response.create",
#             response: { instructions: "বাংলায় বন্ধুসুলভ একটি স্বাগতম বলো।", modalities: ["audio","text"] }
#           }));
#         }catch(e){}
#       };
#       dc.onmessage = function(e){ /* console.log('[oai-events]', e.data); */ };

#       // Remote audio
#       pc.ontrack = function(ev){
#         if(!audio){ audio = new Audio(); audio.autoplay = true; }
#         audio.srcObject = ev.streams[0];
#       };

#       // 3) Mic
#       // Note: getUserMedia works on HTTPS or localhost (127.0.0.1 is fine)
#       mic = await navigator.mediaDevices.getUserMedia({ audio: true });
#       mic.getTracks().forEach(function(t){ pc.addTrack(t, mic); });

#       // 4) Offer
#       var offer = await pc.createOffer();
#       await pc.setLocalDescription(offer);

#       // 5) Send SDP to OpenAI Realtime
#       var hdr = { 'Authorization':'Bearer ' + ek, 'Content-Type':'application/sdp' };
#       if(extraHdr['OpenAI-Beta']) hdr['OpenAI-Beta'] = extraHdr['OpenAI-Beta'];

#       var sr = await fetch(sdpURL, { method:'POST', body: pc.localDescription.sdp, headers: hdr });
#       if(!sr.ok){
#         var txt = await sr.text();
#         throw new Error('SDP failed: ' + sr.status + ' ' + txt);
#       }

#       var ans = await sr.text();
#       await pc.setRemoteDescription({ type:'answer', sdp: ans });

#       inCall = true;
#       btn.classList.add('stop');
#       btn.title = 'Stop Voice';
#       showBadge('Connected'); setTimeout(hideBadge, 1000);
#     }catch(err){
#       console.error('[voice-embed] start failed:', err);
#       showBadge('Error: ' + (err && err.message || err)); setTimeout(hideBadge, 2500);
#       await stop();
#     }finally{
#       btn.disabled = false;
#     }
#   }

#   async function stop(){
#     try{ if(dc) dc.close(); }catch(e){}
#     try{ if(pc) pc.close(); }catch(e){}
#     try{ if(mic) mic.getTracks().forEach(function(t){ t.stop(); }); }catch(e){}
#     dc=null; pc=null; mic=null; inCall=false;
#     btn.classList.remove('stop');
#     btn.title = 'Start Voice';
#     hideBadge();
#   }

#   btn.addEventListener('click', function(){
#     if(!inCall) start(); else stop();
#   });

# })();
# """
#     return HttpResponse(js, content_type="application/javascript")










def embed_js_v2(request):
    js = r"""
(function(){
  'use strict';

  // --- Resolve script tag, public_id, base URL ---
  var s = document.currentScript || (function(){var t=document.getElementsByTagName('script');return t[t.length-1];})();
  var PUBLIC_ID = (s.getAttribute('data-agent') || '').trim();
  var BASE = (s.getAttribute('data-base-url') || (new URL(s.src)).origin || '').trim();
  BASE = BASE.replace(/\/+$/,''); // remove trailing slashes

  if(!PUBLIC_ID){
    console.warn('[voice-embed] Missing data-agent (public_id).');
    return;
  }

  // --- Inject styles ---
  var st = document.createElement('style');
  st.textContent = `
    .va-floating{position:fixed;right:20px;bottom:20px;z-index:2147483647;}
    .va-btn{width:56px;height:56px;border-radius:50%;border:0;background:#16a34a;color:#06130a;font-size:22px;cursor:pointer;box-shadow:0 8px 25px rgba(0,0,0,.25)}
    .va-btn.stop{background:#ef4444;color:#190b0b}
    .va-badge{position:fixed;right:90px;bottom:30px;background:rgba(0,0,0,.75);color:#fff;padding:6px 10px;border-radius:10px;font:13px system-ui;z-index:2147483647;display:none}
    .va-panel{position:fixed;right:20px;bottom:86px;width:320px;max-height:50vh;overflow:auto;background:#0b1220;color:#e5e7eb;border:1px solid #1f2937;border-radius:12px;padding:10px;box-shadow:0 8px 30px rgba(0,0,0,.3);display:none}
    .va-row{display:flex;gap:6px;margin-top:8px}
    .va-input{flex:1;background:#0f172a;border:1px solid #1f2937;border-radius:10px;color:#e5e7eb;padding:8px 10px}
    .va-send{border:0;border-radius:10px;background:#38bdf8;color:#002f47;padding:8px 10px;cursor:pointer}
    .va-chat{display:flex;flex-direction:column;gap:6px}
    .va-bubble{max-width:85%;padding:8px 10px;border-radius:10px;border:1px solid #1f2937;white-space:pre-wrap}
    .va-user{align-self:flex-end;background:#0f172a}
    .va-bot{align-self:flex-start;background:#0b1324}
    .va-disabled-note{padding:10px;border-radius:8px;background:#2b2b2b;color:#f3f3f3;margin-bottom:8px;font-size:13px}
  `;
  document.head.appendChild(st);

  // --- Build UI ---
  var wrap = document.createElement('div'); wrap.className='va-floating';
  var btn  = document.createElement('button'); btn.className='va-btn'; btn.textContent='🎙️'; btn.title='Start Voice';
  var badge = document.createElement('div'); badge.className='va-badge'; badge.textContent='Connecting...';
  var panel = document.createElement('div'); panel.className='va-panel';
  panel.innerHTML = '<div class="va-chat" id="va_chat"></div>'
                  + '<div class="va-row"><input id="va_msg" class="va-input" placeholder="Write a message...">'
                  + '<button id="va_send" class="va-send">Send</button></div>';
  wrap.appendChild(btn);
  document.body.appendChild(wrap);
  document.body.appendChild(badge);
  document.body.appendChild(panel);

  // --- Refs & state ---
  var chatDiv = panel.querySelector('#va_chat');
  var inp     = panel.querySelector('#va_msg');
  var sendBtn = panel.querySelector('#va_send');

  var audio = null, pc=null, dc=null, mic=null, inCall=false;
  var initialInstructions = ""; // filled when /voice/start/ returns
  var initialSent = false;

  function showBadge(t){ badge.textContent=t; badge.style.display='block'; }
  function hideBadge(){ badge.style.display='none'; }
  function bubble(text, who){
    var d=document.createElement('div'); d.className='va-bubble '+who; d.textContent=text;
    chatDiv.appendChild(d); chatDiv.scrollTop=chatDiv.scrollHeight;
  }
  function togglePanel(){ panel.style.display = (panel.style.display==='block'?'none':'block'); }

  // Helper to show a prominent note in chat (e.g., disabled message)
  function showPanelNote(txt){
    var existing = panel.querySelector('.va-disabled-note');
    if(existing) existing.remove();
    var n = document.createElement('div');
    n.className = 'va-disabled-note';
    n.textContent = txt;
    panel.insertBefore(n, panel.firstChild);
  }

  // --- Chat (preflight-free: form-encoded, no custom headers) ---
  async function sendChat(){
    var t=inp.value.trim(); if(!t) return; inp.value=''; bubble(t,'va-user');
    try{
      var body = new URLSearchParams({ message: t });
      var r = await fetch(BASE + '/api/embed/agents/' + PUBLIC_ID + '/chat/', {
        method: 'POST',
        body  : body
      });
      if(r.status === 403){
        showBadge('Agent disabled'); setTimeout(hideBadge, 2500);
        showPanelNote('This agent is currently disabled by the administrator.');
        bubble('⚠️ Agent is disabled.', 'va-bot');
        return;
      }
      var j = await r.json();
      if(!r.ok) throw new Error(j && (j.error || j.detail) || ('status ' + r.status));
      bubble(j.reply || JSON.stringify(j), 'va-bot');
    }catch(err){
      bubble('⚠️ ' + (err && err.message || err), 'va-bot');
    }
  }

  sendBtn.addEventListener('click', sendChat);
  inp.addEventListener('keydown', function(e){ if(e.key==='Enter') sendChat(); });

  // Right-click on mic button toggles chat panel
  btn.addEventListener('contextmenu', function(e){ e.preventDefault(); togglePanel(); });

  // --- Voice (WebRTC) ---
  async function start(){
    btn.disabled = true;
    showBadge('Requesting mic + session...');

    try{
      // 1) Get ephemeral token + initial_instructions from server
      var tr = await fetch(BASE + '/api/embed/agents/' + PUBLIC_ID + '/voice/start/', { method:'POST' });
      var tj_text = await tr.text();
      var tj = {};
      try{ tj = tj_text ? JSON.parse(tj_text) : {}; }catch(e){
        throw new Error('Invalid JSON from voice/start: ' + tj_text);
      }

      if(tr.status === 403){
        showBadge('Agent disabled'); setTimeout(hideBadge, 2500);
        showPanelNote('This agent is currently disabled by the administrator.');
        btn.disabled = false;
        return;
      }

      if(!tr.ok){
        throw new Error(tj && (tj.error || tj.detail) || ('status ' + tr.status));
      }

      var ek = tj.value;
      initialInstructions = (tj.initial_instructions || "").trim();
      var sdpURL = tj.sdp_url || 'https://api.openai.com/v1/realtime?model=gpt-realtime';
      var extraHdr = tj.headers || {};
      if(!ek) throw new Error('No ek received');

      // 2) Create RTCPeerConnection
      pc = new RTCPeerConnection();

      // Optional data channel for realtime events
      dc = pc.createDataChannel('oai-events');
      dc.onopen = function(){
        showBadge('Say something!'); setTimeout(hideBadge, 1200);
        try{
          // send initial instruction if not yet sent
          if(initialInstructions && !initialSent){
            try{
              dc.send(JSON.stringify({
                type: "response.create",
                response: { instructions: initialInstructions, modalities: ["audio","text"] }
              }));
              initialSent = true;
            }catch(e){
              // leave initialSent false so we can retry after SDP
            }
          }
        }catch(e){}
      };
      dc.onmessage = function(e){
        // optional: handle events from provider, e.g. partial transcripts, state
        try{
          var d = JSON.parse(e.data);
          // you can surface events if desired
        }catch(err){}
      };

      // Remote audio
      pc.ontrack = function(ev){
        if(!audio){ audio = new Audio(); audio.autoplay = true; }
        audio.srcObject = ev.streams[0];
      };

      // 3) Mic
      mic = await navigator.mediaDevices.getUserMedia({ audio: true });
      mic.getTracks().forEach(function(t){ pc.addTrack(t, mic); });

      // 4) Offer
      var offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // 5) Send SDP to Realtime provider
      var hdr = { 'Authorization':'Bearer ' + ek, 'Content-Type':'application/sdp' };
      if(extraHdr && extraHdr['OpenAI-Beta']) hdr['OpenAI-Beta'] = extraHdr['OpenAI-Beta'];

      var sr = await fetch(sdpURL, { method:'POST', body: pc.localDescription.sdp, headers: hdr });
      if(!sr.ok){
        var txt = await sr.text();
        throw new Error('SDP failed: ' + sr.status + ' ' + txt);
      }

      var ans = await sr.text();
      await pc.setRemoteDescription({ type:'answer', sdp: ans });

      // Proactively show text immediately so user sees welcome before audio arrives
      if(initialInstructions){
        bubble(initialInstructions, 'va-bot');
      }

      // Ensure initial instruction is sent if not already (some providers only accept after SDP)
      try{
        if(initialInstructions && dc && dc.readyState === 'open' && !initialSent){
          dc.send(JSON.stringify({
            type: "response.create",
            response: { instructions: initialInstructions, modalities: ["audio","text"] }
          }));
          initialSent = true;
        } else if(initialInstructions && dc && dc.readyState !== 'open'){
          // will be sent in dc.onopen
        }
      }catch(e){
        console.warn('[voice-embed] post-SDP initial send failed', e);
      }

      inCall = true;
      btn.classList.add('stop');
      btn.title = 'Stop Voice';
      showBadge('Connected'); setTimeout(hideBadge, 1000);
    }catch(err){
      console.error('[voice-embed] start failed:', err);
      showBadge('Error: ' + (err && err.message || err)); setTimeout(hideBadge, 2500);
      await stop();
    }finally{
      btn.disabled = false;
    }
  }

  async function stop(){
    try{ if(dc) dc.close(); }catch(e){}
    try{ if(pc) pc.close(); }catch(e){}
    try{ if(mic) mic.getTracks().forEach(function(t){ t.stop(); }); }catch(e){}
    dc=null; pc=null; mic=null; inCall=false;
    initialSent = false;
    btn.classList.remove('stop');
    btn.title = 'Start Voice';
    hideBadge();
  }

  btn.addEventListener('click', function(){
    if(!inCall) start(); else stop();
  });

})();
"""
    return HttpResponse(js, content_type="application/javascript")


class EmbedChatJsV1View(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        js = r"""
(function(){
  'use strict';

  // --- Resolve script tag, ids, base URL ---
  var s = document.currentScript || (function(){var t=document.getElementsByTagName('script');return t[t.length-1];})();
  var PUBLIC_ID = (s.getAttribute('data-agent') || '').trim();
  var BASE = (s.getAttribute('data-base-url') || (new URL(s.src)).origin || '').trim();
  BASE = BASE.replace(/\/+$/,''); // remove trailing slashes

  var wsUrl = (s.getAttribute('data-chat-ws') || '').trim();
  var convId = (s.getAttribute('data-conversation') || '').trim();

  var theme = (s.getAttribute('data-theme') || '#016966').trim();
  var themeSoft = (s.getAttribute('data-theme-soft') || '#e6f5f4').trim();
  var teacherName = (s.getAttribute('data-teacher-name') || 'Bartabahok').trim();
  var teacherSubtitle = (s.getAttribute('data-teacher-subtitle') || 'Ask me anything').trim();
  var teacherAvatar = (s.getAttribute('data-teacher-avatar') || '🤖').trim();
  var logoUrl = (s.getAttribute('data-logo-url') || 'https://media.frontliner.io/logo/icon.png').trim();
  var greeting = (s.getAttribute('data-greeting') || '').trim();
  var ownerId = (s.getAttribute('data-owner-id') || '').trim();
  var externalUserId = (s.getAttribute('data-external-user-id') || '').trim();
  var externalUsername = (s.getAttribute('data-external-username') || '').trim();
  var preferredMode = (s.getAttribute('data-chat-mode') || '').trim().toLowerCase();

  function getCookie(name){
    var escaped = name.replace(/[$()*+.?[\\\]^{|}]/g, '\\$&');
    var match = document.cookie.match(new RegExp('(?:^|; )' + escaped + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : '';
  }

  function setCookie(name, value, days){
    try{
      var d = new Date();
      d.setTime(d.getTime() + (days || 30) * 24 * 60 * 60 * 1000);
      document.cookie = name + '=' + encodeURIComponent(value || '')
        + '; path=/; expires=' + d.toUTCString() + '; SameSite=Lax';
    }catch(e){}
  }

  var cookieKeyBase = 'fl_chat_conv_id_' + (PUBLIC_ID || ownerId || 'default');
  var cookieUserIdKey = 'fl_chat_user_id_' + (PUBLIC_ID || ownerId || 'default');
  var cookieUsernameKey = 'fl_chat_user_name_' + (PUBLIC_ID || ownerId || 'default');
  var cookieConv = getCookie(cookieKeyBase);
  if(!convId && cookieConv) convId = cookieConv;
  if(convId) setCookie(cookieKeyBase, convId, 30);

  function randId(){
    return 'guest_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
  }

  if(!externalUserId){
    externalUserId = getCookie(cookieUserIdKey);
  }
  if(!externalUserId){
    externalUserId = randId();
    setCookie(cookieUserIdKey, externalUserId, 30);
  }

  if(!externalUsername){
    externalUsername = getCookie(cookieUsernameKey);
  }
  if(!externalUsername){
    externalUsername = 'Guest';
    setCookie(cookieUsernameKey, externalUsername, 30);
  }

  function hasParam(url, key){
    return new RegExp('[?&]' + key + '=').test(url);
  }

  function appendParams(url, params){
    if(!params.length) return url;
    var hash = '';
    var hashIndex = url.indexOf('#');
    if(hashIndex !== -1){
      hash = url.slice(hashIndex);
      url = url.slice(0, hashIndex);
    }
    var sep = url.indexOf('?') === -1 ? '?' : '&';
    return url + sep + params.join('&') + hash;
  }

  if(!PUBLIC_ID && !wsUrl && !convId && !ownerId){
    console.warn('[embed-chat] Missing data-agent or websocket info.');
  }

  // --- Inject styles ---
  var st = document.createElement('style');
  st.textContent = `
    .ec-floating{position:fixed;right:18px;bottom:18px;z-index:2147483647;font-family:"Merriweather","Georgia",serif;}
    .ec-btn{width:64px;height:64px;border-radius:20px;border:0;background:var(--accent,#016966);color:#f0fffe;font-size:22px;cursor:pointer;box-shadow:0 14px 30px rgba(1,105,102,.35);display:flex;align-items:center;justify-content:center;transition:transform .18s ease,box-shadow .18s ease}
    .ec-btn:hover{transform:translateY(-2px);box-shadow:0 18px 36px rgba(1,105,102,.4)}
    .ec-panel{position:fixed;right:18px;bottom:90px;width:min(360px,92vw);height:min(72vh,560px);background:linear-gradient(180deg,#f8fbfb 0%,#eef6f6 100%);border:1px solid rgba(1,105,102,.18);border-radius:20px;box-shadow:0 20px 50px rgba(1,105,102,.25);display:block;opacity:0;transform:translateY(12px);pointer-events:none;visibility:hidden;transition:all .18s ease;overflow:hidden;color:#0b2f2d}
    .ec-panel.ec-open{opacity:1;transform:translateY(0);pointer-events:auto;visibility:visible}
    .ec-header{display:flex;align-items:center;gap:10px;padding:12px 14px;background:linear-gradient(135deg,var(--accent,#016966),#0a3f3b);color:#eafffe}
    .ec-avatar{width:38px;height:38px;border-radius:12px;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;font-size:20px;overflow:hidden}
    .ec-avatar img{width:100%;height:100%;object-fit:cover;border-radius:12px}
    .ec-btn img{width:38px;height:38px;object-fit:contain}
    .ec-title{flex:1;min-width:0}
    .ec-name{font-weight:700;font-size:14px;letter-spacing:.2px}
    .ec-sub{font-size:11px;opacity:.9}
    .ec-status{display:flex;align-items:center;gap:6px;font-size:11px;opacity:.9}
    .ec-status-dot{width:8px;height:8px;border-radius:50%;background:#65fbd2;box-shadow:0 0 0 3px rgba(101,251,210,.18)}
    .ec-close{border:0;background:transparent;color:#eafffe;font-size:18px;cursor:pointer;padding:4px 6px}
    .ec-body{display:flex;flex-direction:column;height:calc(100% - 62px)}
    .ec-chat{flex:1;overflow:auto;padding:12px;display:flex;flex-direction:column;justify-content:flex-end;gap:8px;background-image:radial-gradient(200px 120px at 20% 0%,rgba(1,105,102,.08),transparent 60%),radial-gradient(220px 140px at 100% 0%,rgba(1,105,102,.06),transparent 55%)}
    .ec-bubble{max-width:86%;padding:10px 12px;border-radius:16px;border:1px solid rgba(1,105,102,.18);background:#fff;box-shadow:0 6px 16px rgba(2,62,60,.08)}
    .ec-label{font-size:10px;text-transform:uppercase;letter-spacing:.8px;opacity:.6;margin-bottom:4px}
    .ec-text{font-size:13px;line-height:1.35;white-space:pre-wrap}
    .ec-user{align-self:flex-end;background:var(--accent-soft,#e6f5f4);border-color:rgba(1,105,102,.25)}
    .ec-bot{align-self:flex-start;background:#ffffff}
    .ec-admin{align-self:flex-start;background:#fff7e6;border-color:#f4d09a}
    .ec-attachments{display:none;flex-wrap:wrap;gap:8px;padding:0 12px 10px}
    .ec-attachment{display:flex;align-items:center;gap:8px;background:#ffffff;border:1px dashed rgba(1,105,102,.2);border-radius:12px;padding:6px 8px;min-width:0}
    .ec-attachment img{width:44px;height:44px;border-radius:10px;object-fit:cover}
    .ec-attachment-meta{min-width:0}
    .ec-attachment-name{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:140px}
    .ec-attachment-size{font-size:10px;opacity:.6}
    .ec-attachment-remove{border:0;background:transparent;color:#9b1c1c;font-size:14px;cursor:pointer}
    .ec-attachment-grid{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
    .ec-attachment-thumb{width:64px;height:64px;border-radius:10px;object-fit:cover;border:1px solid rgba(1,105,102,.2)}
    .ec-attachment-file{display:flex;align-items:center;gap:6px;padding:6px 8px;border-radius:10px;border:1px solid rgba(1,105,102,.18);background:#fff;font-size:11px;max-width:180px}
    .ec-composer{padding:10px 12px;background:linear-gradient(180deg,rgba(255,255,255,.65),rgba(255,255,255,1))}
    .ec-tools{display:flex;gap:6px;margin-bottom:8px}
    .ec-icon{border:1px solid rgba(1,105,102,.25);background:#fff;border-radius:10px;padding:6px 8px;cursor:pointer;font-size:14px}
    .ec-input-row{display:flex;gap:8px;align-items:center}
    .ec-input{flex:1;border:1px solid rgba(1,105,102,.25);border-radius:12px;padding:10px 12px;font-size:13px;outline:none;background:#fff}
    .ec-input:focus{border-color:var(--accent,#016966);box-shadow:0 0 0 3px rgba(1,105,102,.12)}
    .ec-send{border:0;border-radius:12px;background:var(--accent,#016966);color:#eafffe;padding:10px 12px;cursor:pointer;font-weight:600}
    .ec-note{margin:0 12px 8px;padding:8px;border-radius:10px;background:#f4fbfb;border:1px solid rgba(1,105,102,.15);font-size:11px}
    .ec-choice{display:none;flex-direction:column;gap:12px;padding:16px}
    .ec-choice.ec-show{display:flex}
    .ec-choice-card{background:#ffffff;border:1px solid rgba(1,105,102,.18);border-radius:14px;padding:12px 14px;box-shadow:0 8px 20px rgba(2,62,60,.08)}
    .ec-choice-title{font-weight:700;font-size:14px;margin-bottom:4px}
    .ec-choice-desc{font-size:12px;opacity:.7}
    .ec-choice-btn{border:0;border-radius:14px;padding:10px 12px;font-weight:600;cursor:pointer}
    .ec-choice-bot{background:var(--accent,#016966);color:#eafffe}
    .ec-choice-human{background:#ffffff;border:1px solid rgba(1,105,102,.25);color:#0b2f2d}
  `;
  document.head.appendChild(st);

  // --- Build UI ---
  var wrap = document.createElement('div'); wrap.className='ec-floating';
  var btn  = document.createElement('button'); btn.className='ec-btn'; btn.title='Chat';
  if(logoUrl){
    btn.innerHTML = '<img src="' + logoUrl + '" alt="Chat">';
  }else{
    btn.textContent='💬';
  }
  var panel = document.createElement('div'); panel.className='ec-panel';
  panel.innerHTML =
    '<div class="ec-header">'
      + '<div class="ec-avatar" id="ec_avatar"></div>'
      + '<div class="ec-title">'
        + '<div class="ec-name" id="ec_name"></div>'
        + '<div class="ec-sub" id="ec_sub"></div>'
      + '</div>'
      + '<div class="ec-status"><span class="ec-status-dot"></span>Online</div>'
      + '<button class="ec-close" id="ec_close">×</button>'
    + '</div>'
    + '<div class="ec-body">'
      + '<div class="ec-choice" id="ec_choice">'
        + '<div class="ec-choice-card">'
          + '<div class="ec-choice-title">Start a chat</div>'
          + '<div class="ec-choice-desc">Choose who you want to talk with.</div>'
        + '</div>'
        + '<button class="ec-choice-btn ec-choice-bot" id="ec_choice_bot">Chat with AI Assistant</button>'
        + '<button class="ec-choice-btn ec-choice-human" id="ec_choice_human">Chat with Human</button>'
      + '</div>'
      + '<div class="ec-chat" id="ec_chat"></div>'
      + '<div class="ec-attachments" id="ec_attachments"></div>'
      + '<div class="ec-composer">'
        + '<div class="ec-tools">'
          + '<button class="ec-icon" id="ec_image_btn" title="Add image">🖼️</button>'
          + '<button class="ec-icon" id="ec_file_btn" title="Add file">📎</button>'
          + '<input id="ec_image_input" type="file" accept="image/*" multiple style="display:none">'
          + '<input id="ec_file_input" type="file" multiple style="display:none">'
        + '</div>'
        + '<div class="ec-input-row">'
          + '<input id="ec_msg" class="ec-input" placeholder="Ask to Bartabahok...">'
          + '<button id="ec_send" class="ec-send">Send</button>'
        + '</div>'
      + '</div>'
    + '</div>';
  wrap.appendChild(btn);
  document.body.appendChild(wrap);
  document.body.appendChild(panel);

  // --- Refs & state ---
  panel.style.setProperty('--accent', theme || '#016966');
  panel.style.setProperty('--accent-soft', themeSoft || '#e6f5f4');

  var chatDiv = panel.querySelector('#ec_chat');
  var attachDiv = panel.querySelector('#ec_attachments');
  var inp     = panel.querySelector('#ec_msg');
  var sendBtn = panel.querySelector('#ec_send');
  var composer = panel.querySelector('.ec-composer');
  var imgBtn = panel.querySelector('#ec_image_btn');
  var fileBtn = panel.querySelector('#ec_file_btn');
  var imgInput = panel.querySelector('#ec_image_input');
  var fileInput = panel.querySelector('#ec_file_input');
  var closeBtn = panel.querySelector('#ec_close');
  var choiceWrap = panel.querySelector('#ec_choice');
  var choiceBot = panel.querySelector('#ec_choice_bot');
  var choiceHuman = panel.querySelector('#ec_choice_human');

  panel.querySelector('#ec_name').textContent = teacherName || 'Bartabahok';
  panel.querySelector('#ec_sub').textContent = teacherSubtitle || 'Ask me anything';
  var avatarEl = panel.querySelector('#ec_avatar');
  if(avatarEl){
    if(logoUrl){
      avatarEl.innerHTML = '<img src="' + logoUrl + '" alt="' + (teacherName || 'Logo') + '">';
    }else{
      avatarEl.textContent = teacherAvatar || '🤖';
    }
  }

  var ws = null;
  var pending = [];
  var pendingEcho = [];
  var attachments = [];
  var maxAttachments = 6;
  var chatMode = (preferredMode === 'bot' || preferredMode === 'human') ? preferredMode : '';

  function formatSize(bytes){
    if(!bytes && bytes !== 0) return '';
    if(bytes < 1024) return bytes + ' B';
    var kb = bytes / 1024;
    if(kb < 1024) return kb.toFixed(1) + ' KB';
    var mb = kb / 1024;
    if(mb < 1024) return mb.toFixed(1) + ' MB';
    return (mb / 1024).toFixed(1) + ' GB';
  }

  function bubble(text, who, label, atts){
    var d = document.createElement('div'); d.className='ec-bubble ' + who;
    if(label){
      var l = document.createElement('div'); l.className='ec-label'; l.textContent = label;
      d.appendChild(l);
    }
    if(text){
      var p = document.createElement('div'); p.className='ec-text'; p.textContent = text;
      d.appendChild(p);
    }
    if(atts && atts.length){
      var grid = document.createElement('div'); grid.className='ec-attachment-grid';
      atts.forEach(function(a){
        if(a.isImage && a.dataUrl){
          var img = document.createElement('img');
          img.className='ec-attachment-thumb';
          img.src = a.dataUrl;
          img.alt = a.name || 'image';
          grid.appendChild(img);
        }else{
          var chip = document.createElement('div');
          chip.className = 'ec-attachment-file';
          chip.textContent = '📎 ' + (a.name || 'file');
          grid.appendChild(chip);
        }
      });
      d.appendChild(grid);
    }
    chatDiv.appendChild(d);
    chatDiv.scrollTop = chatDiv.scrollHeight;
  }

  function setChoiceVisible(show){
    if(!choiceWrap) return;
    if(show){
      choiceWrap.classList.add('ec-show');
      chatDiv.style.display = 'none';
      attachDiv.style.display = 'none';
      if(composer) composer.style.display = 'none';
    }else{
      choiceWrap.classList.remove('ec-show');
      chatDiv.style.display = '';
      if(composer) composer.style.display = '';
      renderAttachments();
    }
  }

  function setChatMode(mode){
    chatMode = (mode === 'bot') ? 'bot' : 'human';
    setChoiceVisible(false);
    if(resolveWsUrl()){
      ensureWs();
    }
  }

  function togglePanel(){
    panel.classList.toggle('ec-open');
    if(panel.classList.contains('ec-open')){
      if(!chatMode){
        setChoiceVisible(true);
      }else{
        setChoiceVisible(false);
      }
    }
  }

  function showNote(txt){
    var n = document.createElement('div');
    n.className = 'ec-note';
    n.textContent = txt;
    panel.querySelector('.ec-body').insertBefore(n, attachDiv);
  }

  function resolveWsUrl(){
    if(wsUrl){
      var extra = [];
      if(ownerId && !hasParam(wsUrl, 'owner_id')) extra.push('owner_id=' + encodeURIComponent(ownerId));
      if(externalUserId && !hasParam(wsUrl, 'external_user_id')) extra.push('external_user_id=' + encodeURIComponent(externalUserId));
      if(externalUsername && !hasParam(wsUrl, 'external_username')) extra.push('external_username=' + encodeURIComponent(externalUsername));
      return appendParams(wsUrl, extra);
    }
    if(!chatMode) return '';
    var baseForWs = (BASE || (window.location && window.location.origin) || '').trim();
    if(!baseForWs) return '';
    var wsBase = baseForWs.replace(/^http/i, 'ws');
    var path = (chatMode === 'bot') ? '/ws/chat/bot/' : '/ws/chat/direct/';
    if(convId) path += convId + '/';
    var qs = [];
    if(ownerId) qs.push('owner_id=' + encodeURIComponent(ownerId));
    if(externalUserId) qs.push('external_user_id=' + encodeURIComponent(externalUserId));
    if(externalUsername) qs.push('external_username=' + encodeURIComponent(externalUsername));
    if(qs.length) path += '?' + qs.join('&');
    return wsBase.replace(/\/+$/,'') + path;
  }

  function roleMeta(senderType){
    var s = (senderType || '').toLowerCase();
    if(s === 'admin') return { klass: 'ec-admin', label: teacherName || 'Bartabahok' };
    if(s === 'bot') return { klass: 'ec-bot', label: 'Assistant' };
    return { klass: 'ec-user', label: 'You' };
  }

  function normalizeAttachments(raw){
    var out = [];
    (raw || []).forEach(function(a){
      var name = a && a.name || 'file';
      var type = a && a.type || '';
      var dataUrl = a && (a.dataUrl || a.data || a.data_url || a.preview) || '';
      var isImage = !!(a && (a.is_image || (type && type.indexOf('image/') === 0)));
      out.push({ name: name, type: type, dataUrl: dataUrl, isImage: isImage, size: a && a.size || 0 });
    });
    return out;
  }

  function handleIncoming(data){
    if(data && data.type === 'conversation_init'){
      if(data.conversation_id){
        convId = String(data.conversation_id);
        setCookie(cookieKeyBase, convId, 30);
      }
      return;
    }
    var text = data && (data.message || data.text || data.reply) || '';
    var meta = roleMeta(data && data.sender_type);
    var atts = normalizeAttachments(data && data.attachments);
    if(!text && !atts.length) return;
    if(text && pendingEcho.length && text === pendingEcho[0]){
      pendingEcho.shift();
      return;
    }
    bubble(text, meta.klass, meta.label, atts);
  }

  function ensureWs(){
    if(!wsUrl && !chatMode){
      setChoiceVisible(true);
      return false;
    }
    if(!wsUrl && !convId && !ownerId){
      showNote('Missing owner id or conversation id.');
      return false;
    }
    var url = resolveWsUrl();
    if(!url) return false;
    if(ws && (ws.readyState === 0 || ws.readyState === 1)) return true;
    try{
      ws = new WebSocket(url);
    }catch(e){
      console.warn('[embed-chat] ws create failed:', e);
      return false;
    }
    ws.onopen = function(){
      while(pending.length){
        var payload = pending.shift();
        try{
          ws.send(JSON.stringify(payload));
          if(payload.text){ pendingEcho.push(payload.text); }
        }catch(e){}
      }
    };
    ws.onmessage = function(ev){
      try{ handleIncoming(JSON.parse(ev.data)); }catch(err){}
    };
    ws.onerror = function(){
      showNote('Chat socket error. Retrying on next message.');
    };
    ws.onclose = function(){
      // will reconnect when user sends next message
    };
    return true;
  }

  function sendViaWs(text, atts){
    if(!ensureWs()){
      bubble('⚠️ Chat websocket not configured.', 'ec-bot', 'Assistant');
      return;
    }
    var payload = { text: text || '' };
    if(atts && atts.length) payload.attachments = atts;
    if(ws.readyState === 1){
      try{
        ws.send(JSON.stringify(payload));
        if(payload.text){ pendingEcho.push(payload.text); }
      }catch(e){
        bubble('⚠️ Failed to send.', 'ec-bot', 'Assistant');
      }
      return;
    }
    pending.push(payload);
  }

  function renderAttachments(){
    if(!chatMode){
      attachDiv.style.display = 'none';
      return;
    }
    attachDiv.innerHTML = '';
    if(!attachments.length){
      attachDiv.style.display = 'none';
      return;
    }
    attachDiv.style.display = 'flex';
    attachments.forEach(function(att){
      var item = document.createElement('div');
      item.className = 'ec-attachment';
      if(att.isImage && att.dataUrl){
        var img = document.createElement('img');
        img.src = att.dataUrl;
        img.alt = att.name || 'image';
        item.appendChild(img);
      }
      var meta = document.createElement('div');
      meta.className = 'ec-attachment-meta';
      var name = document.createElement('div');
      name.className = 'ec-attachment-name';
      name.textContent = att.name || 'file';
      var size = document.createElement('div');
      size.className = 'ec-attachment-size';
      size.textContent = formatSize(att.size);
      meta.appendChild(name);
      meta.appendChild(size);
      item.appendChild(meta);
      var rm = document.createElement('button');
      rm.className = 'ec-attachment-remove';
      rm.textContent = '✕';
      rm.addEventListener('click', function(){
        attachments = attachments.filter(function(a){ return a.id !== att.id; });
        renderAttachments();
      });
      item.appendChild(rm);
      attachDiv.appendChild(item);
    });
  }

  function addFiles(fileList){
    var files = Array.prototype.slice.call(fileList || []);
    files.forEach(function(file){
      if(attachments.length >= maxAttachments) return;
      var isImage = file && file.type && file.type.indexOf('image/') === 0;
      var att = {
        id: 'att_' + Date.now() + '_' + Math.random().toString(36).slice(2,7),
        name: file.name,
        type: file.type || 'application/octet-stream',
        size: file.size || 0,
        isImage: isImage,
        dataUrl: ''
      };
      attachments.push(att);
      if(isImage){
        var reader = new FileReader();
        reader.onload = function(e){
          att.dataUrl = e.target.result;
          renderAttachments();
        };
        reader.readAsDataURL(file);
      }
    });
    renderAttachments();
  }

  function serializeAttachments(){
    return attachments.map(function(a){
      return {
        name: a.name,
        type: a.type,
        size: a.size,
        is_image: a.isImage,
        data: a.dataUrl || ''
      };
    });
  }

  if(chatMode){
    setChoiceVisible(false);
  }else{
    setChoiceVisible(true);
  }

  async function sendChat(){
    if(!chatMode){
      setChoiceVisible(true);
      return;
    }
    var t = inp.value.trim();
    if(!t && !attachments.length) return;

    var payloadAtts = serializeAttachments();
    bubble(t, 'ec-user', 'You', normalizeAttachments(payloadAtts));
    inp.value = '';
    attachments = [];
    renderAttachments();

    if(resolveWsUrl()){
      sendViaWs(t, payloadAtts);
      return;
    }
    if(chatMode !== 'bot'){
      bubble('⚠️ Chat websocket not configured.', 'ec-bot', 'Assistant');
      return;
    }
    // Fallback: public chat endpoint (bot only) if websocket not provided
    if(payloadAtts.length){
      showNote('Attachments require websocket chat. Sending text only.');
      if(!t) return;
    }
    if(!PUBLIC_ID || !BASE){
      bubble('⚠️ Missing base URL or agent id.', 'ec-bot', 'Assistant');
      return;
    }
    try{
      var body = new URLSearchParams({ message: t });
      var r = await fetch(BASE + '/api/embed/agents/' + PUBLIC_ID + '/chat/', { method: 'POST', body: body });
      var j = await r.json();
      if(!r.ok) throw new Error(j && (j.error || j.detail) || ('status ' + r.status));
      bubble(j.reply || JSON.stringify(j), 'ec-bot', 'Assistant');
    }catch(err){
      bubble('⚠️ ' + (err && err.message || err), 'ec-bot', 'Assistant');
    }
  }

  btn.addEventListener('click', togglePanel);
  closeBtn.addEventListener('click', togglePanel);
  if(choiceBot) choiceBot.addEventListener('click', function(){ setChatMode('bot'); });
  if(choiceHuman) choiceHuman.addEventListener('click', function(){ setChatMode('human'); });
  sendBtn.addEventListener('click', sendChat);
  inp.addEventListener('keydown', function(e){ if(e.key==='Enter') sendChat(); });

  imgBtn.addEventListener('click', function(){ imgInput.click(); });
  fileBtn.addEventListener('click', function(){ fileInput.click(); });
  imgInput.addEventListener('change', function(){ addFiles(imgInput.files); imgInput.value=''; });
  fileInput.addEventListener('change', function(){ addFiles(fileInput.files); fileInput.value=''; });

  if(greeting){
    bubble(greeting, 'ec-admin', teacherName || 'Bartabahok');
  }

})();
"""
        return HttpResponse(js, content_type="application/javascript")
