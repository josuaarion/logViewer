using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Soduko_solver
{
    public partial class Form1 : Form
    {
        private bord board;
        private bool[,] fixedValues;
        private TextBox[] UIbox;
        private bool cancel = false;
        public Form1()
        {
            InitializeComponent();
            button2.Hide();
            this.UIbox = new TextBox[81]{ aa, ba, ca, da, ea, fa, ga, ha, ia,
                                          ab, bb, cb, db, eb, fb, gb, hb, ib, 
                                          ac, bc, cc, dc, ec, fc, gc, hc, ic, 
                                          ad, bd, cd, dd, ed, fd, gd, hd, id, 
                                          ae, be, ce, de, ee, fe, ge, he, ie, 
                                          af, bf, cf, df, ef, ff, gf, hf, if_, 
                                          ag, bg, cg, dg, eg, fg, gg, hg, ig, 
                                          ah, bh, ch, dh, eh, fh, gh, hh, ih, 
                                          ai, bi, ci, di, ei, fi, gi, hi, ii };

        }

        private bool isSetUpAllowed()
        {
            if (this.board.isValid())
            {
                return true;
            }
            return false;
        }

        private void button1_Click(object sender, EventArgs e)
        {
            button2.Hide();
            initializeBord();
            findExistingnumbers();
            if (!isSetUpAllowed())
            {
                var result = MessageBox.Show("The puzzle has no solution. \n Want to try another?", "Error", MessageBoxButtons.YesNo);

                if (result == DialogResult.No)
                {
                    Application.Exit();
                }
                else
                {
                    resetSelected();
                    return;
                }
            }

            int[] cellIndex = findMostFilled();

            int[] cellCounter = this.decrement(cellIndex);

            bord solution = solver(cellCounter,this.board);
            bool isSolved = checkCorrectness(solution);

            if (isSolved)
            {
                fillSolution(solution);
                button1.Hide();
                Clear.Enabled = false;
                button2.Show();

            }
            else
            {
                var result = MessageBox.Show("The puzzle has no solution. \n Want to try another?", "Error", MessageBoxButtons.YesNo);

                if (result == DialogResult.No)
                {
                    Application.Exit();
                }
                else
                {
                    resetSelected();
                }
            }

        }

        public int[] findMostFilled()
        {
            return this.board.findBestCell();
        }

        public void resetSelected()
        {
            
                for (int i = 0; i < 9; i++)
                {
                    for (int ii = 0; ii < 9; ii++)
                    {
                        int index = (i * 9) + ii;
                        int[] c = { i, ii };
                        if (!this.fixedValues[i, ii])
                        {
                            this.UIbox[index].Text = "";
                            this.UIbox[index].Enabled = true;
                            this.UIbox[index].BackColor = System.Drawing.Color.White;
                            this.board.removeValue(c);
                        }
                        else
                        {
                            this.UIbox[index].Enabled = true;
                            this.UIbox[index].BackColor = System.Drawing.Color.White;
                        }
                    }
                }
            
        }
        public void clearForm()
        {

            foreach (TextBox x in UIbox)
            {
                x.Text = "";
                x.Enabled = true;
                x.BackColor = System.Drawing.Color.White;
            }
        }

        private bool checkCorrectness(bord test)
        {
            if (!test.isFull())
            {
                return false;
            }
            return true;
        }
        private void fillSolution(bord bordid)
        {
            for (int i = 0; i < 9; i++)
            {
                for (int ii = 0; ii < 9; ii++)
                {
                    int index = (i * 9) + ii;
                    int[] c = { i, ii };
                    this.UIbox[index].Text = bordid.getValue(c);
                    this.UIbox[index].Enabled = false;
                }
            }
                
            
        }

        private int[] increment(int[] counter)
        {
            
            if (counter[1] < 8)
            {
                counter[1]++;
            }
            else if (counter[0] < 8)
            {
                counter[1] = 0;
                counter[0]++;
            }
            else
            {
                counter[0] = 0;
                counter[1] = 0;
            }
            return counter;
        }

        private int[] decrement(int[] counter)
        {

            if (counter[1] > 0)
            {
                counter[1]--;
            }
            else if (counter[0] > 0)
            {
                counter[1] = 8;
                counter[0]--;
            }
            else
            {
                counter[0] = 8;
                counter[1] = 8;
            }
            return counter;
        }

        private bord solver(int[] counter, bord bor)
        {
            counter = increment(counter);
            if (bor.isFull())
            {
                return bor;
            }

            while (bor.isOccu(counter))
            {
                counter = increment(counter);
            }
            for (int i = 1; i < 10; i++)
            {
                if (bor.check(counter, i))
                {
                   bor.setValue(counter, i);

                   bor = solver(counter, bor);
                   if (bor.isFull())
                   {
                       return bor;
                   }
                }
                
            }
            bor.removeValue(counter);
            counter = decrement(counter);
            while (this.fixedValues[counter[0], counter[1]])
            {
                counter = decrement(counter);    
            }

            return bor;
        }

        public void findExistingnumbers()
        {

            for (int i = 0; i < 9; i++)
            {
                for (int ii = 0; ii < 9; ii++)
                {
                    int index = (i * 9) + ii;

                    if(this.UIbox[index].Text != ""){
                        int[] c = { i, ii };
                        this.board.setValue(c, int.Parse(this.UIbox[index].Text));
                        this.fixedValues[i, ii] = true;
                        this.UIbox[index].Enabled = false;
                        this.UIbox[index].BackColor = System.Drawing.Color.YellowGreen;
                    }
                }
            }

            
        }

        public void initializeBord()
        {
            line[] rows = { new line(), new line(), new line(), new line(), new line(), new line(), new line(), new line(), new line() };

            line[] cols = { new line(), new line(), new line(), new line(), new line(), new line(), new line(), new line(), new line() };

            box[] boxes = { new box(), new box(), new box(), new box(), new box(), new box(), new box(), new box(), new box() };

            cell[,] bord = new cell[9, 9];

            for (int i = 0; i < 9; i++)
            {
                for (int ii = 0; ii < 9; ii++)
                {

                    int index;

                    if (i < 3)
                    {
                        if (ii < 3)
                        {
                            index = 0;
                        }
                        else if (ii < 6)
                        {
                            index = 1;
                        }
                        else
                        {
                            index = 2;
                        }
                    }
                    else if (i < 6)
                    {
                        if (ii < 3)
                        {
                            index = 3;
                        }
                        else if (ii < 6)
                        {
                            index = 4;
                        }
                        else
                        {
                            index = 5;
                        }
                    }
                    else
                    {
                        if (ii < 3)
                        {
                            index = 6;
                        }
                        else if ( ii < 6)
                        {
                            index = 7;
                        }
                        else
                        {
                            index = 8;
                        }
                    }

                    bord[i, ii] = new cell(rows[i], cols[ii], boxes[index], 0);
                }
            }

            bord bordid = new bord(bord);
            this.board = bordid;
            this.fixedValues = new bool[9, 9];
        }

        private void button2_Click(object sender, EventArgs e)
        {
            resetSelected();
            button2.Hide();
            button1.Show();
            Clear.Enabled = true;
        }

        private void ii_KeyPress_1(object sender, KeyPressEventArgs e)
        {
            
            if (e.KeyChar == '0')
            {
                e.Handled = true;
            }

            if (!char.IsControl(e.KeyChar) && !char.IsDigit(e.KeyChar) &&(e.KeyChar != '.') )
            {
                
                e.Handled = true;
                
            }
        }

        private void Clear_Click(object sender, EventArgs e)
        {
            initializeBord();
            clearForm();
        }

        private void canc_Click(object sender, EventArgs e)
        {

        }

    }
}
