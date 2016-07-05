# Defines functions for this feature
use strict;
use warnings;
our (%text, %config);
our $module_name;
our $captcha;
our %miniserv;
our $signup_domains_file;

require 'virtualmin-signup-lib.pl';

# feature_name()
# Returns a short name for this feature
sub feature_name
{
return $text{'feat_name'};
}

# feature_losing(&domain)
# Returns a description of what will be deleted when this feature is removed
sub feature_losing
{
return $text{'feat_losing'};
}

# feature_label(in-edit-form)
# Returns the name of this feature, as displayed on the domain creation and
# editing form
sub feature_label
{
my ($edit) = @_;
return $edit ? $text{'feat_label2'} : $text{'feat_label'};
}

sub feature_hlink
{
return 'feat';
}

# feature_check()
# Returns undef if all the needed programs for this feature are installed,
# or an error message if not
sub feature_check
{
if ($config{'captcha'}) {
	my $captcha = &create_captcha_object();
	if (!$captcha) {
		return $text{'feat_ecaptcha'};
		}
	}
return undef;
}

# feature_depends(&domain)
# Returns undef if all pre-requisite features for this domain are enabled,
# or an error message if not
sub feature_depends
{
if ($_[0]->{'alias'}) {
	return $text{'feat_ealias'};
	}
elsif (!$_[0]->{'mail'} &&
       (!defined(&virtual_server::can_users_without_mail) ||
	!&virtual_server::can_users_without_mail($_[0]))) {
	return $text{'feat_email'};
	}
else {
	return undef;
	}
}

# feature_clash(&domain)
# Returns undef if there is no clash for this domain for this feature, or
# an error message if so
sub feature_clash
{
return undef;	# cannot ever clash
}

# feature_suitable([&parentdom], [&aliasdom], [&subdom])
# Returns 1 if some feature can be used with the specified alias and
# parent domains
sub feature_suitable
{
return !$_[1] && !$_[2];		# not possible for aliases
}

# feature_setup(&domain)
# Called when this feature is added, with the domain object as a parameter
sub feature_setup
{
# Grant anonymous access to this module, and add this server to its allowed list
&$virtual_server::first_print($text{'feat_setup'});
&foreign_require("acl", "acl-lib.pl");
&lock_file($ENV{'MINISERV_CONFIG'});
if (defined(&acl::setup_anonymous_access)) {
	&acl::setup_anonymous_access("/$module_name", $module_name);
	}
else {
	my %miniserv;
	&get_miniserv_config(\%miniserv);
	my @anon = split(/\s+/, $miniserv{'anonymous'});
	my $found = 0;
	foreach my $a (@anon) {
		my ($aurl, $auser) = split(/=/, $a);
		$found++ if ($aurl eq "/$module_name");
		}
	if (!$found) {
		# Find the first user who can use this module
		my (%acl, $auser);
		&read_acl(undef, \%acl);
		if ($config{'anonuser'}) {
			$auser = $config{'anonuser'};
			}
		else {
			foreach my $u (keys %acl) {
				$auser = $u
				   if (&indexof($module_name, @{$acl{$u}}) >= 0);
				}
			$auser ||= "root";
			}
		push(@anon, "/$module_name=$auser");
		$miniserv{'anonymous'} = join(" ", @anon);
		&put_miniserv_config(\%miniserv);
		&virtual_server::register_post_action(
			defined(&main::restart_webmin) ?
			   \&main::restart_webmin : \&virtual_server::restart_webmin);
		}
	}
&unlock_file($ENV{'MINISERV_CONFIG'});

&lock_file($signup_domains_file);
my @doms = &list_signup_domains();
&save_signup_domains(@doms, $_[0]->{'dom'});
&unlock_file($signup_domains_file);
my ($port, $proto) = &get_miniserv_port_proto();
&$virtual_server::second_print(&text('feat_url',
	"$proto://$_[0]->{'dom'}:$port/$module_name/"));
}

# get_miniserv_port_proto()
# Returns the port number and protocol (http or https) for Webmin
sub get_miniserv_port_proto
{
if ($ENV{'SERVER_PORT'}) {
	# Running under miniserv
	return ( $ENV{'SERVER_PORT'},
		 $ENV{'HTTPS'} eq 'ON' ? 'https' : 'http' );
	}
else {
	# Get from miniserv config
	my %miniserv;
	&get_miniserv_config(\%miniserv);
	return ( $miniserv{'port'},
		 $miniserv{'ssl'} ? 'https' : 'http' );
	}
}

# feature_modify(&domain, &olddomain)
# Called when a domain with this feature is modified
sub feature_modify
{
if ($_[0]->{'dom'} ne $_[1]->{'dom'}) {
	# Update domain in allowed list
	&$virtual_server::first_print($text{'feat_save'});
	&lock_file($signup_domains_file);
	my @doms = &list_signup_domains();
	foreach my $l (@doms) {
		$l = $_[0]->{'dom'} if ($l eq $_[1]->{'dom'});
		}
	&save_signup_domains(@doms);
	&unlock_file($signup_domains_file);
	&$virtual_server::second_print($virtual_server::text{'setup_done'});
	}
}

# feature_delete(&domain)
# Called when this feature is disabled, or when the domain is being deleted
sub feature_delete
{
&$virtual_server::first_print($text{'feat_delete'});
&lock_file($signup_domains_file);
my @doms = &list_signup_domains();
@doms = grep { $_ ne $_[0]->{'dom'} } @doms;
&save_signup_domains(@doms);
&unlock_file($signup_domains_file);
&$virtual_server::second_print($virtual_server::text{'setup_done'});
}

# feature_webmin(&main-domain, &all-domains)
# Returns a list of webmin module names and ACL hash references to be set for
# the Webmin user when this feature is enabled
# (optional)
sub feature_webmin
{
# XXX doesn't need to do anything, because the signup module is granted
#     access anonymously
return ( );
}

# feature_import(domain-name, user-name, db-name)
# Returns 1 if this feature is already enabled for some domain being imported,
# or 0 if not
sub feature_import
{
foreach my $l (&list_signup_domains()) {
	return 1 if ($l eq $_[0]);
	}
return 0;
}

1;
