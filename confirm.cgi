#!/usr/local/bin/perl
# Validate inputs and tell the user what will be done
use strict;
use warnings;
our (%text, %in, %config);

require './virtualmin-signup-lib.pl';
&ReadParse();
&error_setup($text{'confirm_err'});
no warnings "once";
my $oldvm = $virtual_server::module_info{'version'} < 2.93;
use warnings "once";

# Validate inputs
my @doms = &list_signup_domains();
&indexof($in{'dom'}, @doms) >= 0 || &error($text{'confirm_edom'});
my $d = &virtual_server::get_domain_by("dom", $in{'dom'});
$d || &error($text{'confirm_edom2'});
$in{'user'} =~ /^[a-z0-9\.\-\_]+$/ || &error($text{'confirm_euser'});

# Check captcha
if ($config{'captcha'} == 1 && $in{'confirm'}) {
	my $captcha = &create_captcha_object();
	if ($captcha) {
		my $c = $captcha->check_code($in{'captcha'}, $in{'md5'});
		$c == 1 || &error($text{'confirm_ecaptcha'});
		}
	}
elsif ($config{'captcha'} == 2 && $in{'confirm'}) {
  my $recaptcha = &create_recaptcha_object();
  if ($recaptcha) {
    my $c = $recaptcha->check_answer($config{'recaptcha_privkey'},$ENV{'REMOTE_ADDR'},
                        $in{'recaptcha_challenge_field'}, $in{'recaptcha_response_field'});
    $c->{is_valid} || &error($text{'confirm_ecaptcha'});
    }
  }

# Build the user object
my $user = &virtual_server::create_initial_user($d);
my (%taken, %utaken);
&virtual_server::build_taken(\%taken, \%utaken);
if ($user->{'unix'} && !$user->{'webowner'}) {
	# UID needs to be unique
	$user->{'uid'} = &virtual_server::allocate_uid(\%taken);
	}
else {
	# UID is same as domain for Qmail users and web owners
	$user->{'uid'} = $d->{'uid'};
	}
$user->{'gid'} = $d->{'gid'};
$user->{'real'} = $in{'real'};
$user->{'plainpass'} = $in{'pass'};
if ($oldvm) {
	my $salt = substr(time(), -2);
	$user->{'pass'} = crypt($in{'pass'}, $salt);
	}
else {
	$user->{'pass'} = &virtual_server::encrypt_user_password(
				$user, $user->{'plainpass'});
	}
$user->{'passmode'} = 3;
$user->{'shell'} ||= $virtual_server::config{'shell'};
if (!$user->{'noprimary'}) {
	$user->{'email'} = $user->{'email'} || $oldvm ?
			$in{'user'}."\@".$d->{'dom'} : undef;
	}

# Add configured settings
$user->{'quota'} = $config{'quota'} if ($config{'quota'} ne '');
$user->{'mquota'} = $config{'quota'} if ($config{'quota'} ne '');
$user->{'qquota'} = $config{'qquota'} if ($config{'qquota'} ne '');
$user->{'shell'} = $config{'shell'} if ($config{'shell'} ne '');

# Check for a username clash
my @users = &virtual_server::list_domain_users($d);
my ($clash) = grep { $_->{'user'} eq $in{'user'} &&
		  $_->{'unix'} == $user->{'unix'} } @users;
$clash && &error($virtual_server::text{'user_eclash2'});

# Work out the real username
if (($utaken{$in{'user'}} || ($d && $virtual_server::config{'append'})) &&
    !$user->{'noappend'}) {
	# Need to append domain name
	$user->{'user'} = &virtual_server::userdom_name($in{'user'},$d);
	}
else {
	# Username is as entered
	$user->{'user'} = $in{'user'};
	}

if ($user->{'unix'}) {
	# Check for a Unix clash
	if ($utaken{$user->{'user'}} ||
	    &virtual_server::check_clash($in{'user'}, $d->{'dom'})) {
		&error($virtual_server::text{'user_eclash'});
		}
	}

# Check if the name is too long
my $lerr;
if ($user->{'unix'} && ($lerr = &virtual_server::too_long($user->{'user'}))) {
	&error($lerr);
	}

# Work out home directory
$user->{'home'} = "$d->{'home'}/$virtual_server::config{'homes_dir'}/$in{'user'}";
if (-e $user->{'home'} && !$user->{'fixedhome'}) {
	&error(&virtual_server::text('user_emkhome', $user->{'home'}));
	}

# Set mail file location
if ($user->{'qmail'}) {
	&virtual_server::userdom_substitutions($user, $d);
	$user->{'mailstore'} = &virtual_server::substitute_template(
		$virtual_server::config{'ldap_mailstore'}, $user);
	}

if (defined(&virtual_server::validate_user)) {
	# Validate user
	my $err = &virtual_server::validate_user($d, $user);
	&error($err) if ($err);
	}

# Check limits
if (!$oldvm) {
	my ($mleft, $mreason, $mmax) = &virtual_server::count_feature(
					"mailboxes", $d->{'user'});
	$mleft == 0 && &error($virtual_server::text{'user_emailboxlimit'});
	}

if ($in{'confirm'}) {
	# Do it!
	&ui_print_header(undef, $text{'create_title'}, "");

	print $text{'create_doing'},"<p>\n";
	&virtual_server::create_user($user, $d);

	if ($user->{'home'} && !$user->{'nocreatehome'}) {
		# Create home dir
		if ($oldvm) {
			&system_logged("mkdir -p ".quotemeta($user->{'home'}));
                        &system_logged("chown $user->{'uid'}:$user->{'gid'} ".
				       quotemeta($user->{'home'}));
                        &system_logged("chmod 755 ".quotemeta($user->{'home'}));
			&virtual_server::copy_skel_files(
				$virtual_server::config{'mail_skel'}, $user,
				$user->{'home'});
			}
		else {
			&virtual_server::create_user_home($user);
			}
		}

	if ($user->{'email'}) {
		# Create mail file
                &virtual_server::create_mail_file($user);
                }

	if ($user->{'email'} || !$in{'email_def'}) {
		# Send signup email
		&virtual_server::send_user_email($d, $user,
			$in{'email_def'} ? undef : $in{'email'}, 0);
		}

	if ($oldvm && $user->{'unix'}) {
		# Set quotas
		if ($virtual_server::config{'home_quotas'}) {
			&virtual_server::set_quota($user->{'user'},
				   $virtual_server::config{'home_quotas'},
				   $config{'defmquota'});
			}
		if ($virtual_server::config{'mail_quotas'} &&
		    $virtual_server::config{'mail_quotas'} ne
		      $virtual_server::config{'home_quotas'}) {
			&virtual_server::set_quota($user->{'user'},
				   $virtual_server::config{'mail_quotas'},
				   $config{'defmquota'});
			}
		}

	&virtual_server::run_post_actions();
	print $virtual_server::text{'setup_done'},"<p>\n";

	&ui_print_footer("", $text{'index_return'});
	}
else {
	# Ask the user if he is sure, and show details
	&ui_print_header(undef, $text{'confirm_title'}, "");

	print &ui_form_start("confirm.cgi", "post");
	foreach my $i (keys %in) {
		print &ui_hidden($i, $in{$i}),"\n";
		}
	print &ui_table_start($text{'confirm_header'}, undef, 2);

	print &ui_table_row($text{'confirm_user'}, "<tt>$in{'user'}</tt>");
	print &ui_table_row($text{'confirm_unix'}, "<tt>$user->{'user'}</tt>");
	print &ui_table_row($text{'confirm_real'}, "<tt>$in{'real'}</tt>");
	if ($user->{'email'}) {
		print &ui_table_row($text{'confirm_email'},
				    "<tt>$user->{'email'}</tt>");
		}
	print &ui_table_row($text{'confirm_ftp'},
	  $user->{'shell'} eq $virtual_server::config{'shell'} ?
		$text{'no'} : $text{'yes'});
	if ($virtual_server::config{'home_quotas'}) {
		print &ui_table_row($text{'confirm_quota'},
		   $user->{'quota'} ?
			&nice_size($user->{'quota'}*&virtual_server::quota_bsize($virtual_server::config{'home_quotas'})) : $text{'confirm_unlimit'});
		}

	if ($config{'captcha'} == 1) {
		# Captcha image
		my $captcha = &create_captcha_object();
		if ($captcha) {
			my $md5 = $captcha->generate_code(6);
			print &ui_table_row($text{'index_captcha'},
				&ui_textbox("captcha", undef, 6)."<br>".
				"<img src=captcha.cgi?md5=$md5>");
			print &ui_hidden("md5", $md5),"\n";
			}
		}
  elsif($config{'captcha'} == 2) {
    my $recaptcha = &create_recaptcha_object();
    if ($recaptcha) {
			print &ui_table_row($text{'index_captcha'},
            $recaptcha->get_html($config{'recaptcha_pubkey'}), undef, 1);
      }
    }

	&clear_captcha_images();

	print &ui_table_end();
	print &ui_form_end([ [ "confirm", $text{'confirm_confirm'} ] ]);

	&ui_print_footer("", $text{'index_return'});
	}
