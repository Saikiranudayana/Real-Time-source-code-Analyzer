/* ══════════════════════════════════════════════════
   CodeLens — app.js
   jQuery-powered interactions
   ══════════════════════════════════════════════════ */

$(function () {

  /* ── Smooth scroll ─────────────────────────────── */
  function scrollToSection(id) {
    var $el = $('#' + id);
    if ($el.length) {
      $('html, body').animate({ scrollTop: $el.offset().top }, 500, 'swing');
    }
  }

  // Nav buttons
  $(document).on('click', '[data-scroll]', function () {
    scrollToSection($(this).data('scroll'));
  });

  /* ── Video fade-in / fade-out loop ─────────────── */
  (function initVideo() {
    var video = document.getElementById('bg-video');
    if (!video) return;

    var FADE = 0.5; // seconds

    function loop() {
      var t = video.currentTime;
      var d = video.duration;
      if (!d || isNaN(d)) { requestAnimationFrame(loop); return; }

      var opacity = 1;
      if (t < FADE)          opacity = t / FADE;
      else if (t > d - FADE) opacity = (d - t) / FADE;

      video.style.opacity = Math.max(0, Math.min(1, opacity)).toFixed(3);
      requestAnimationFrame(loop);
    }

    video.addEventListener('ended', function () {
      video.style.opacity = '0';
      setTimeout(function () {
        video.currentTime = 0;
        video.play().catch(function () {});
      }, 100);
    });

    video.addEventListener('canplay', function () {
      video.play().catch(function () {});
      requestAnimationFrame(loop);
    });
  })();

  /* ── Input focus ring ──────────────────────────── */
  $(document).on('focus', '.repo-input', function () {
    $(this).css('box-shadow', '0 0 0 2px hsl(262 83% 58% / 0.4)');
  }).on('blur', '.repo-input', function () {
    $(this).css('box-shadow', '0 0 0 0px transparent');
  });

  /* ── Helper: escape HTML ──────────────────────── */
  function esc(str) {
    return $('<div>').text(String(str)).html();
  }

  /* ── Ingest form ─────────────────────────────── */
  $('#ingest-form').on('submit', function (e) {
    e.preventDefault();

    var url    = $('#repo-url').val().trim();
    var $btn    = $('#ingest-btn');
    var $status = $('#ingest-status');

    if (!url) return;

    $btn.prop('disabled', true).text('Indexing…').css('opacity', '0.6');
    $status
      .removeClass('status-success status-error')
      .addClass('status-loading')
      .text('⏳ Cloning and indexing repository — this may take a minute…')
      .show();

    $.ajax({
      url: '/chatbot',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ github_url: url }),
      success: function (data) {
        $status
          .removeClass('status-loading status-error')
          .addClass('status-success')
          .text('✅ ' + (data.message || 'Repository indexed successfully. Head to the chat section!'));
        scrollToSection('chat');
      },
      error: function (xhr) {
        var msg = 'Indexing failed';
        try { msg = JSON.parse(xhr.responseText).error || msg; } catch (_) {}
        $status
          .removeClass('status-loading status-success')
          .addClass('status-error')
          .text('❌ ' + msg);
      },
      complete: function () {
        $btn.prop('disabled', false).text('Analyze Repository').css('opacity', '1');
      }
    });
  });

  /* ── Chat: send message ──────────────────────── */
  function sendMessage() {
    var $input    = $('#chat-input');
    var $messages = $('#chat-messages');
    var question  = $input.val().trim();
    if (!question) return;

    $input.val('');

    // User bubble
    var $user = $(
      '<div class="chat-bubble-user rounded-2xl rounded-tr-sm px-4 py-3 max-w-[85%]">' +
        '<p class="text-sm leading-6" style="color:hsl(40 6% 95%);">' + esc(question) + '</p>' +
      '</div>'
    );
    $messages.append($user);

    // Typing indicator
    var $typing = $(
      '<div class="chat-bubble-bot rounded-2xl rounded-tl-sm px-4 py-3">' +
        '<div class="typing"><span></span><span></span><span></span></div>' +
      '</div>'
    );
    $messages.append($typing);
    $messages.scrollTop($messages[0].scrollHeight);

    $.ajax({
      url: '/get',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ question: question }),
      success: function (data) {
        var answer = data.answer || data.result || data.response || JSON.stringify(data);
        $typing.html(
          '<p class="text-sm leading-6 whitespace-pre-wrap" style="color:hsl(40 6% 95%);">' +
          esc(answer) + '</p>'
        );
      },
      error: function (xhr) {
        var msg = 'Request failed';
        try { msg = JSON.parse(xhr.responseText).error || msg; } catch (_) {}
        $typing.html(
          '<p class="text-sm leading-6" style="color:hsl(0 84% 70%);">⚠️ ' + esc(msg) + '</p>'
        );
      },
      complete: function () {
        $messages.scrollTop($messages[0].scrollHeight);
      }
    });
  }

  // Send on button click
  $('#send-btn').on('click', sendMessage);

  // Send on Enter key
  $('#chat-input').on('keydown', function (e) {
    if (e.key === 'Enter') { sendMessage(); }
  });

});
