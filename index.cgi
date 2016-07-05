#!/usr/local/bin/perl
# Show a page for entering details of a new user account
use strict;
use warnings;
our (%text, %in, %config);

require './virtualmin-signup-lib.pl';
my @doms = &list_signup_domains();
@doms || &error($text{'index_edoms'});

&ui_print_header(undef, $text{'index_title'}, "", undef, 0, 1);

print &ui_form_start("confirm.cgi", "get");
print &ui_table_start($text{'index_header'}, undef, 2);

# Domain to create in
if (@doms > 1) {
	my $host = $ENV{'HTTP_HOST'};
	my $dom;
	foreach my $d (@doms) {
		$dom = $d if ($d =~ /\Q$host\E/i);
		}
	if ($config{'autodom'} && $dom) {
		# Force one domain
		print &ui_table_row($text{'index_dom'}, "<tt>$dom</tt>");
		print &ui_hidden("dom", $dom),"\n";
		}
	else {
		# Allow selection
		print &ui_table_row($text{'index_dom'},
			&ui_select("dom", $dom, [ map { [ $_ ] } @doms ]));
		}
	}
else {
	# Only one domain anyway
	print &ui_table_row($text{'index_dom'}, "<tt>$doms[0]</tt>");
	print &ui_hidden("dom", $doms[0]),"\n";
	}

# Username
print &ui_table_row($text{'index_user'}, &ui_textbox("user", undef, 20));

# Password
print &ui_table_row($text{'index_pass'}, &ui_password("pass", undef, 20));

# Real name
print &ui_table_row($text{'index_real'}, &ui_textbox("real", undef, 40));

# Email address
print &ui_table_row($text{'index_email'},
		  &ui_opt_textbox("email", undef, 30, $text{'index_emaildef'}));

print &ui_table_end();
print &ui_form_end([ [ "signup", $text{'index_signup'} ] ]);

&ui_print_footer();
