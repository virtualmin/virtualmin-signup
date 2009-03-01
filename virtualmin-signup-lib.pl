# Functions for creating a new mailbox user
# XXX captcha
# XXX Apache proxy from website's /signup URL

BEGIN { push(@INC, ".."); };
eval "use WebminCore;";
if ($@) {
	do '../web-lib.pl';
	do '../ui-lib.pl';
	}
&init_config();
&foreign_require("virtual-server", "virtual-server-lib.pl");

$signup_domains_file = "$module_config_directory/signup";
$captcha_data_dir = "$module_config_directory/data";
$captcha_images_dir = "$module_config_directory/images";

sub list_signup_domains
{
local @rv;
open(DOMS, $signup_domains_file);
while(<DOMS>) {
	s/\r|\n//g;
	push(@rv, $_);
	}
close(DOMS);
return @rv;
}

# save_signup_domains(dom, ...)
sub save_signup_domains
{
&open_tempfile(DOMS, ">$signup_domains_file");
foreach my $d (@_) {
	&print_tempfile(DOMS, $d,"\n");
	}
&close_tempfile(DOMS);
}

sub create_captcha_object
{
eval "use Authen::Captcha";
return undef if ($@);
local $captcha = Authen::Captcha->new();
if (!-d $captcha_data_dir) {
	mkdir($captcha_data_dir, 0700);
	}
$captcha->data_folder($captcha_data_dir);
if (!-d $captcha_images_dir) {
	mkdir($captcha_images_dir, 0700);
	}
$captcha->output_folder($captcha_images_dir);
$captcha->expire(3000);
$captcha->keep_failures(1);
return $captcha;
}

sub clear_captcha_images
{
opendir(DIR, $captcha_images_dir);
foreach my $f (readdir(DIR)) {
	local @st = stat("$captcha_images_dir/$f");
	if (time() - $st[9] > 24*60*60) {
		unlink("$captcha_images_dir/$f");
		}
	}
closedir(DIR);
}

1;

