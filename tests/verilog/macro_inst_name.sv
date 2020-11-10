module mymod (
);

`define MY_TOP mysubmod
`define MY_INST u_mysubmod

  `MY_TOP
#(
  .param1(param1),
  .param2(param2)
 )
 `MY_INST (
   .clk(clk)
);

endmodule