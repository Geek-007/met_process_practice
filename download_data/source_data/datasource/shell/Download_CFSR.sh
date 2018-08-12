#! /bin/csh -f
# Usage: Download CFSR reanalysis data to specific dir
# Args: $1-password $2-username $3-year $4-mon $5-dir

set passwd = $1
set username = $2
set year = $3
set i = $4 
set dir = $5

set num_chars = `echo "$passwd" |awk '{print length($0)}'`
if ($num_chars == 0) then
  echo "You need to set your password before you can continue"
  echo "  see the documentation in the script"
  exit
endif
@ num = 1
set newpass = ""
while ($num <= $num_chars)
  set c = `echo "$passwd" |cut -b{$num}-{$num}`
  if ("$c" == "&") then
    set c = "%26";
  else
    if ("$c" == "?") then
      set c = "%3F"
    else
      if ("$c" == "=") then
        set c = "%3D"
      endif
    endif
  endif
  set newpass = "$newpass$c"
  @ num ++
end
set passwd = "$newpass"
#
set cert_opt = ""
wget $cert_opt -O auth_status.rda.ucar.edu --save-cookies auth.rda.ucar.edu.$$ --post-data="email=$username&passwd=$passwd&action=login" https://rda.ucar.edu/cgi-bin/login

## current year
## set year = `date +%Y`
set opts = "-P $dir/$year -N"
set mons = (01 02 03 04 05 06 07 08 09 10 11 12)

wget $cert_opt $opts --load-cookies auth.rda.ucar.edu.$$ rda.ucar.edu/data/ds094.1/$year/tmax.cdas1.$year$mons[$i].grb2
wget $cert_opt $opts --load-cookies auth.rda.ucar.edu.$$ rda.ucar.edu/data/ds094.1/$year/tmp2m.cdas1.$year$mons[$i].grb2
wget $cert_opt $opts --load-cookies auth.rda.ucar.edu.$$ rda.ucar.edu/data/ds094.1/$year/tmin.cdas1.$year$mons[$i].grb2
wget $cert_opt $opts --load-cookies auth.rda.ucar.edu.$$ rda.ucar.edu/data/ds094.1/$year/rh2m.cdas1.$year$mons[$i].grb2
wget $cert_opt $opts --load-cookies auth.rda.ucar.edu.$$ rda.ucar.edu/data/ds094.1/$year/apcp.cdas1.$year$mons[$i].grb2
wget $cert_opt $opts --load-cookies auth.rda.ucar.edu.$$ rda.ucar.edu/data/ds094.1/$year/wnd10m.cdas1.$year$mons[$i].grb2
wget $cert_opt $opts --load-cookies auth.rda.ucar.edu.$$ rda.ucar.edu/data/ds094.1/$year/dswsfc.cdas1.$year$mons[$i].grb2


