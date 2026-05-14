#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const urlPath = path.join(__dirname, 'APP_URL.txt');
const registryPath = path.join(__dirname, 'URL_REGISTRY.txt');
const templatePath = path.join(__dirname, 'www', 'index.template.html');
const htmlPath = path.join(__dirname, 'www', 'index.html');

let url = '';
if (fs.existsSync(urlPath)) {
  const lines = fs.readFileSync(urlPath, 'utf8').split('\n');
  for (const line of lines) {
    const trimmed = line.replace(/^#.*/, '').trim();
    if (trimmed && trimmed.startsWith('http')) {
      url = trimmed;
      break;
    }
  }
}

if (!url || !url.startsWith('http')) {
  console.log('APP_URL.txt에 서버 URL을 입력하세요. (예: https://xxxx.trycloudflare.com)');
  process.exit(1);
}

let urlRegistry = '';
if (fs.existsSync(registryPath)) {
  const lines = fs.readFileSync(registryPath, 'utf8').split('\n');
  for (const line of lines) {
    const trimmed = line.replace(/^#.*/, '').trim();
    if (trimmed && trimmed.startsWith('http')) {
      urlRegistry = trimmed;
      break;
    }
  }
}

const srcPath = fs.existsSync(templatePath) ? templatePath : htmlPath;
let html = fs.readFileSync(srcPath, 'utf8');
html = html.replace(/URL_REGISTRY_PLACEHOLDER/g, urlRegistry || '');
html = html.replace(/APP_URL_PLACEHOLDER/g, url);
fs.writeFileSync(htmlPath, html);
console.log('URL 설정 완료:', urlRegistry ? '(동적 모드) ' + urlRegistry : url);
