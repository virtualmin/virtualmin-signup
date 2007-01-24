#!/usr/local/bin/perl
# Output one Captcha image

require './virtualmin-signup-lib.pl';
&ReadParse();
$in{'md5'} =~ /^[a-z0-9]+$/ || &error($text{'md5_emd5'});
open(IMAGE, "$captcha_images_dir/$in{'md5'}.png") ||
	&error($text{'md5_efile'});
print "Content-type: image/png\n\n";
while(<IMAGE>) {
	print;
	}
close(IMAGE);


