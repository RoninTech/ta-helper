---
title: Search the Site
featured_image: "https://lh3.googleusercontent.com/pw/ACtC-3erYwpThzgDNNtp3VeXe8jIiu7-hw6wv3Awqw3jS8DKxDdarqfOp-ua31OsPXMrKbJRkWOYIW5fa19AB9YnQIv6-09Jg75ptBNTvVwZh-KWcvozDYhgOEUDMNYF-D59YSAduf_Uz4o-MIgoB39O6dmToQ=w1216-h912-no"
images:
  - "https://lh3.googleusercontent.com/pw/ACtC-3erYwpThzgDNNtp3VeXe8jIiu7-hw6wv3Awqw3jS8DKxDdarqfOp-ua31OsPXMrKbJRkWOYIW5fa19AB9YnQIv6-09Jg75ptBNTvVwZh-KWcvozDYhgOEUDMNYF-D59YSAduf_Uz4o-MIgoB39O6dmToQ=w1216-h912-no"
omit_header_text: true
description: Find anything on the website.
draft: false
author: "Paul"
---

<p>
    Powered by <a href="https://github.com/cloudcannon/pagefind">Pagefind</a> by&nbsp;<a href="https://cloudcannon.com">CloudCannon</a>.<br>Requires JavaScript.
</p>

<link href="/_pagefind/pagefind-ui.css" rel="stylesheet">
<script src="/_pagefind/pagefind-ui.js" type="text/javascript"></script>
<div id="search"></div>
<script>
  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  const searchString = urlParams.get("q");
  window.addEventListener('DOMContentLoaded', (event) => {
    let pagefind = new PagefindUI({ element: "#search" });
    if (searchString) { 
      pagefind.triggerSearch(searchString);
    }
  });
  waitForElm(".pagefind-ui__search-input").then((elm) => {
    elm.focus();
  });
function waitForElm(selector) {
  return new Promise((resolve) => {
    if (document.querySelector(selector)) {
      return resolve(document.querySelector(selector));
    }
    const observer = new MutationObserver((mutations) => {
      if (document.querySelector(selector)) {
        resolve(document.querySelector(selector));
        observer.disconnect();
      }
    });
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  });
}
</script>

#### Example Searches

Find all articles [by Paul](/search/?q=%22By%20Paul%22)  

Find all articles [by Helen](/search/?q=%22By%20Helen%22)  

Find all mentions of [coffee](/search/?q=coffee)