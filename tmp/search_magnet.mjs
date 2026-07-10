import axios from 'axios';
import * as cheerio from 'cheerio';

const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
];

function randomUA() {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

async function searchBaidu(query, max = 5) {
  try {
    const url = `https://www.baidu.com/s?wd=${encodeURIComponent(query)}&rn=${max}`;
    const resp = await axios.get(url, {
      headers: { 'User-Agent': randomUA(), 'Accept': 'text/html' },
      timeout: 15000,
    });
    const $ = cheerio.load(resp.data);
    const results = [];
    $('.result, .c-container').each((i, el) => {
      const titleEl = $(el).find('h3 a');
      const title = titleEl.text().trim();
      const link = titleEl.attr('href') || '';
      const abstract = $(el).find('.c-abstract, .content-right_8Zs40').text().trim();
      if (title) results.push({ title, link, abstract, source: 'baidu' });
    });
    return results.slice(0, max);
  } catch (e) {
    console.error(`Baidu error: ${e.message}`);
    return [];
  }
}

async function searchSogou(query, max = 5) {
  try {
    const url = `https://www.sogou.com/web?query=${encodeURIComponent(query)}`;
    const resp = await axios.get(url, {
      headers: { 'User-Agent': randomUA(), 'Accept': 'text/html' },
      timeout: 15000,
    });
    const $ = cheerio.load(resp.data);
    const results = [];
    $('.vrwrap, .rb').each((i, el) => {
      const titleEl = $(el).find('h3 a, .vr-title a');
      const title = titleEl.text().trim();
      const link = titleEl.attr('href') || '';
      const abstract = $(el).find('.star-wiki, .str-text').text().trim();
      if (title) results.push({ title, link, abstract, source: 'sogou' });
    });
    return results.slice(0, max);
  } catch (e) {
    console.error(`Sogou error: ${e.message}`);
    return [];
  }
}

// 检查结果中是否包含磁力链接关键字
function hasMagnet(item) {
  const text = (item.title + ' ' + item.abstract).toLowerCase();
  return text.includes('magnet') || text.includes('磁力') || text.includes('btih') || text.includes('torrent');
}

async function main() {
  const queries = [
    'JAV 4K 2160p 无码 磁力链接',
    'uncensored 4K jav torrent magnet btih',
    'HEYZO 4K 2160p magnet 种子',
    'javdb magnet 4K uncensored download',
  ];

  const allResults = [];

  for (const q of queries) {
    process.stdout.write(`\n🔍 ${q}\n`);
    process.stdout.write('─'.repeat(60) + '\n');
    
    const [baiduRes, sogouRes] = await Promise.all([
      searchBaidu(q, 5),
      searchSogou(q, 5),
    ]);
    
    const combined = [...baiduRes, ...sogouRes];
    allResults.push(...combined);
    
    for (const r of combined) {
      const tag = r.source === 'baidu' ? 'B' : 'S';
      const magnet = hasMagnet(r) ? ' ⭐磁力' : '';
      process.stdout.write(`[${tag}] ${r.title.slice(0, 80)}\n`);
      process.stdout.write(`      ${r.link.slice(0, 100)}\n`);
      if (magnet) process.stdout.write(`      ${magnet}\n`);
    }
    
    if (combined.length === 0) process.stdout.write('  (无结果)\n');
  }

  // 专门搜 magnet 链接关键词
  process.stdout.write(`\n\n🎯 专门搜索磁力链接:\n`);
  process.stdout.write('═'.repeat(60) + '\n');
  
  const magnetQueries = [
    'javdb 磁力 链接 4K',
    'magnet:?xt=urn:btih 4K uncensored',
  ];

  for (const q of magnetQueries) {
    process.stdout.write(`\n🔍 ${q}\n`);
    const r = await searchSogou(q, 10);
    for (const item of r) {
      const m = hasMagnet(item) ? ' ⭐磁力' : '';
      process.stdout.write(`[S] ${item.title.slice(0, 80)}${m}\n`);
      process.stdout.write(`      ${item.link.slice(0, 100)}\n`);
    }
  }
}

main().catch(console.error);
