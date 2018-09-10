#coding: utf8

'''
What's CDN? CDN stands for Content Delivery Network. You can see more about CDN on wikipedia.

Some useful tips:
the site is behind a CDN but the CDN is "invisible". i.e the response code from site domain.example is 404 Not Found, but it's actually using a CDN with another server header. You can try lookup via DNS.


Please note that i am not responsible for any damage caused through use of this script.


Author: RedFoX a.k.a. bluesec7
License: FreeLicense

Any suggestions are welcome :D
'''



import sys, requests, urlparse
from dns.resolver import query, NoAnswer, NXDOMAIN, NoNameservers


__author__ = 'RedFoX'
CDN_list = {'cloudfront.net':'Amazon Cloudfront', 'cloudflare.com':'CloudFlare'} # You can add self by looking on CNAME or NS result


class NeedArguments(Exception):
	pass

def find_cdn(a):
	for cdn_ in CDN_list.keys():
		if cdn_ in a:
			return CDN_list[cdn_] # we have found that

def lookup(domain):
	'Lookup if domain is using CDN. This is "bad" CDN lookup coz it use known CDN list to find if the domain use CDN.'
	print('Looking up via DNS..')
	CDNs = []
	print('Checking Multiple IP...')
	try:
		asw = query(domain)
	except NXDOMAIN:
		raise NXDOMAIN("Are you sure %r exist?"%domain)
	except NoNameservers:
		raise NoNameservers('No nameserver found for %r'%domain)
	except NoAnswer:
		raise NoAnswer('No IP for %s!'%domain)
	print('Found IP: %s'%[str(a.address) for a in asw ])
	
		
	#print('Probably %s is using CDN (maybe :P)!'%domain)
	# check whether domain is using CNAME (but doesn't mean it's use CDN..)
	print('Checking CNAME...')
	try:
		asw = query(domain, 'cname')
		domains =  [ a.to_text() for a in asw ]
		print('Found that %s have another domains: %s'%(domain,','.join(domains)))
		for d in domains:
			cdn_found = find_cdn(d)
			if cdn_found:
				print('Got CDN from CNAME!')
				if cdn_found not in CDNs:
					CDNs.append(cdn_found)
			
	except NoAnswer as err:
		print('No CNAME found!')
	
	print('Checking NS...')
	try:
		asw = query(domain, 'ns')
		print('Found Nameservers: %s'% ','.join([ a.to_text() for a in asw ]))
	except NoAnswer:
		print('No Nameserver? Perhaps you can try SOA query instead')
	else:
		print('Checking CDN from NS..')
		for a in asw:
			ns = a.to_text()
			cdn_found = find_cdn(ns)
			if cdn_found:
				print('Got CDN from NS!')
				if cdn_found not in CDNs:
					CDNs.append(cdn_found)
	if CDNs:
		print('CDN used by %s : %s'%(domain, ','.join(CDNs)))
	else:
		print('No CDN used by %s'%domain)

def lookup_by_http(url):
	print('Looking up via HTTP..')
	domain = urlparse.urlparse(url).netloc
	h = {
	'host':'KNTL',
	'connection':'close'
	}
	r = requests.head(url, headers=h)
	if r.status_code == 403 and r.reason.lower() == 'forbidden':
		cdn = 'unknown'
		if 'server' in r.headers:
			cdn = r.headers['server'].title()
		print('%s is using %s CDN'%(domain, cdn))
	else:
		print('No CDN used by %s!'%domain)
		print('The result is %d %s'%(r.status_code, r.reason))
	


if __name__=='__main__':
	if len(sys.argv) < 2:
		e = "Too few arguments.."
		raise NeedArguments(e)
	else:
		domain = sys.argv[1] 
		lookup(domain)
		print('Trying http..')
		lookup_by_http('http://'+domain)
		print('Trying https..')
		try:
			lookup_by_http('https://'+domain)
		except requests.exceptions.SSLError:
			print('There is an SSL error while trying to connect to %s! Aborted'%domain)
	