<html>
   <body>
       <div>
           <form action="https://myserverurl.com/some-endpoint" method="post">
               ${csrf_input | n}
               <label for="fname">First name:</label><br>
               <input type="text" id="fname" name="fname">
               <label for="lname">Last name:</label><br>
               <input type="text" id="lname" name="lname">
           </form>
       </div>
   </body>
</html>
