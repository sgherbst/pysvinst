// ref: https://github.com/sgherbst/pysvinst/issues/5

module my_module (
    input i_clk,
    output o_clk
);
    assign o_clk = i_clk;
endmodule

module gen_test #(
    parameter n=2
) (
  input logic i_clk,
  output logic [(n-1):0] o_clks
);

  genvar i;
  generate
    for (i=0; i<n; i++) begin : generate_test
      my_module my_module_inst (
        .i_clk(i_clk),
        .o_clk(o_clks[i])
      );
    end : generate_test
  endgenerate

endmodule