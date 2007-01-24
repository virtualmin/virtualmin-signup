#!/usr/local/bin/perl
# Show a page for entering details of a new user account

require './virtualmin-signup-lib.pl';
@doms = &list_signup_domains();
@doms || &error($text{'index_edoms'});

&ui_print_header(undef, $text{'index_title'}, "", undef, 0, 1);

print &ui_form_start("confirm.cgi", "post");
print &ui_table_start($text{'index_header'}, undef, 2);

# Domain to create in
if (@doms > 1) {
	$host = $ENV{'HTTP_HOST'};
	foreach $d (@doms) {
		$dom = $d if ($d =~ /\Q$host\E/i);
		}
	print &ui_table_row($text{'index_dom'},
		&ui_select("dom", $dom, [ map { [ $_ ] } @doms ]));
	}
else {
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

