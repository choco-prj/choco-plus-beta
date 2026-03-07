// オートコンプリート機能
console.log('autocomplete.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded fired');
    
    // ヘッダーの検索入力
    const headerInput = document.getElementById('search-input');
    console.log('headerInput element:', headerInput);
    
    // ホームページの検索入力を探す
    const allQInputs = document.querySelectorAll('input[name="q"]');
    console.log('All inputs with name="q":', allQInputs);
    
    // 両方の検索入力に対して処理
    const inputs = Array.from(allQInputs);
    console.log('Processing inputs:', inputs.length);
    
    inputs.forEach((input, idx) => {
        console.log(`Setting up autocomplete for input ${idx}:`, input);
        
        // 候補箱を作成
        const suggestBox = document.createElement('div');
        suggestBox.className = 'suggest-box';
        suggestBox.style.display = 'none';
        
        // 親要素に相対位置を設定
        let container = input.parentElement;
        console.log('Parent container:', container);
        
        if (container && container.style.position !== 'relative') {
            container.style.position = 'relative';
        }
        
        container.appendChild(suggestBox);
        console.log('suggestBox appended to container');
        
        let timeout;
        
        // 入力イベント
        input.addEventListener('input', async function() {
            clearTimeout(timeout);
            
            const query = this.value.trim();
            console.log('入力イベント:', query, '要素ID:', input.id, '名前:', input.name);
            
            if (query.length < 2) {
                console.log('入力が2文字未満、ボックスを隠す');
                suggestBox.style.display = 'none';
                return;
            }
            
            // サーバーから候補を取得
            timeout = setTimeout(async () => {
                try {
                    let suggestions = [];
                    
                    // バックエンドAPIから候補を取得
                    try {
                        const apiUrl = `/api/suggestions?q=${encodeURIComponent(query)}`;
                        console.log('APIを呼び出し:', apiUrl);
                        
                        const response = await fetch(apiUrl);
                        if (response.ok) {
                            suggestions = await response.json();
                            console.log('取得した候補:', suggestions);
                        } else {
                            console.warn('API応答エラー:', response.status);
                            suggestions = [query];
                        }
                    } catch (apiError) {
                        console.warn('バックエンドAPI呼び出し失敗:', apiError);
                        // フォールバック：クエリをそのまま返す
                        suggestions = [query];
                    }
                    
                    // 候補がない場合でもボックスを表示（動作確認用）
                    console.log('Suggestions array:', suggestions);
                    
                    if (!suggestions || suggestions.length === 0) {
                        console.log('候補がありません - 空のボックスを表示');
                        // 空のボックスを表示して動作を確認
                        suggestBox.innerHTML = '<div style="padding: 10px 20px; color: #999; text-align: center;">検索中...</div>';
                    } else {
                        // 候補を表示
                        suggestBox.innerHTML = suggestions
                            .map(s => `<div class="suggest-item">${escapeHtml(s)}</div>`)
                            .join('');
                        
                        console.log('候補ボックスのHTML設定完了:', suggestBox.innerHTML.substring(0, 50));
                    }
                    
                    // 位置を調整
                    const rect = input.getBoundingClientRect();
                    const parentRect = input.parentElement.getBoundingClientRect();
                    
                    suggestBox.style.left = (rect.left - parentRect.left) + 'px';
                    suggestBox.style.top = (rect.bottom - parentRect.top) + 'px';
                    suggestBox.style.width = rect.width + 'px';
                    suggestBox.style.zIndex = '10000';
                    suggestBox.style.display = 'block';
                    
                    console.log('候補ボックス表示:', {
                        left: suggestBox.style.left,
                        top: suggestBox.style.top,
                        width: suggestBox.style.width,
                        display: suggestBox.style.display,
                        suggestionCount: suggestions.length
                    });
                    
                    // 候補をクリックしたら値をセット
                    document.querySelectorAll('.suggest-item').forEach(item => {
                        item.addEventListener('click', function() {
                            input.value = this.innerText;
                            suggestBox.style.display = 'none';
                            input.form.submit();
                        });
                    });
                } catch (error) {
                    console.error('検索候補の取得に失敗:', error);
                    // エラーでもボックスを表示
                    suggestBox.innerHTML = '<div style="padding: 10px 20px; color: #999; text-align: center;">エラー</div>';
                    suggestBox.style.display = 'block';
                }
            }, 300);
        });
        
        // フォーカス時に候補を表示
        input.addEventListener('focus', async function() {
            if (this.value.length >= 2) {
                // 既に候補がある場合は表示
                if (suggestBox.innerHTML) {
                    suggestBox.style.display = 'block';
                }
            }
        });
        
        // クリック外で候補を隠す
        document.addEventListener('click', function(e) {
            if (e.target !== input && !suggestBox.contains(e.target)) {
                suggestBox.style.display = 'none';
            }
        });
    });
    
    // HTML特殊文字をエスケープ
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
});
