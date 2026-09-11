document$.subscribe(function() {
  mermaid.initialize({ startOnLoad: true });
  mermaid.init(undefined, document.querySelectorAll('code.language-mermaid'));
})
