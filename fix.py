import sys
with open('templates/login.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
old_text_pattern = re.compile(r'function startFaceDetection\(video\) \{.*?function closeFaceLogin\(\) \{', re.DOTALL)

new_text = r"""function startFaceDetection(video) {
            const canvas = document.getElementById('faceCanvas');
            const container = document.getElementById('faceVideoContainer');
            let attemptCount = 0;
            const MAX_ATTEMPTS = 30; // ~15 seconds at 2 checks/sec

            container.classList.add('scanning');
            container.style.borderColor = '';
            document.getElementById('faceStatus').innerHTML = '<div class="text-indigo-600"><i class="fas fa-eye mr-2"></i>Scanning for face...</div>';

            faceDetectionInterval = setInterval(async () => {
                attemptCount++;
                if (attemptCount > MAX_ATTEMPTS) {
                    clearInterval(faceDetectionInterval);
                    container.classList.remove('scanning');
                    document.getElementById('faceStatus').innerHTML = `
                        <div class="text-amber-600 mb-3"><i class="fas fa-exclamation-triangle mr-2"></i>No face recognized.</div>
                        <button type="button" onclick="startFaceDetection(document.getElementById('faceVideo'))" class="w-full py-2 bg-indigo-50 text-indigo-700 font-bold rounded-xl hover:bg-indigo-100 transition text-sm">
                            <i class="fas fa-sync mr-2"></i>Try Again
                        </button>
                    `;
                    return;
                }

                try {
                    const detection = await faceapi.detectSingleFace(video).withFaceLandmarks().withFaceDescriptor();
                    if (detection) {
                        // Face detected
                        container.classList.remove('scanning');
                        container.style.borderColor = 'rgba(16,185,129,0.8)';

                        document.getElementById('faceStatus').innerHTML = '<div class="flex items-center justify-center gap-2 text-emerald-600"><div class="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div><span>Face detected! Verifying...</span></div>';
                        clearInterval(faceDetectionInterval);

                        const descriptor = Array.from(detection.descriptor);
                        const csrfInput = document.querySelector('input[name="csrf_token"]');
                        const csrfToken = csrfInput ? csrfInput.value : '';

                        const resp = await fetch('/auth/face-login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken, 'X-CSRF-Token': csrfToken },
                            body: JSON.stringify({ descriptor })
                        });
                        const result = await resp.json();

                        if (result.success) {
                            const confStr = result.confidence !== undefined ? result.confidence : '--';
                            document.getElementById('faceStatus').innerHTML = `<div class="text-emerald-600"><i class="fas fa-check-circle mr-2"></i>${result.message}<br><span class="text-xs text-gray-400">Confidence: ${confStr}%</span></div>`;
                            setTimeout(() => { window.location.href = result.redirect; }, 1200);
                        } else {
                            container.style.borderColor = 'rgba(239,68,68,0.8)';
                            document.getElementById('faceStatus').innerHTML = `<div class="text-red-600 mb-3"><i class="fas fa-times-circle mr-2"></i>${result.message}</div>
                            <button type="button" onclick="startFaceDetection(document.getElementById('faceVideo'))" class="w-full py-2 bg-indigo-50 text-indigo-700 font-bold rounded-xl hover:bg-indigo-100 transition text-sm">
                                <i class="fas fa-sync mr-2"></i>Try Again
                            </button>`;
                        }
                    }
                } catch (e) {
                    console.error('Detection error:', e);
                }
            }, 500);
        }

        function closeFaceLogin() {"""

if old_text_pattern.search(text):
    text = old_text_pattern.sub(new_text, text)
    with open('templates/login.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed.")
else:
    print("Pattern not found.")
