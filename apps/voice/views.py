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