using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Soduko_solver
{
    class cell
    {
        line row;
        line col;
        box box;
        int value;

        public cell(line row, line col, box box, int value)
        {
            this.row = row;
            this.col = col;
            this.box = box;
            this.value = value;
        }

        public void setValue(int index1, int index2, int[] index3, int value)
        {
            this.row.set(index1, value);
            this.col.set(index2, value);
            this.box.set(index3, value);
            this.value = value;
            return;
        }

        public void removeValue(int index1, int index2, int[] index3)
        {
            this.row.remove(index1);
            this.col.remove(index2);
            this.box.remove(index3);
            this.value = 0;
            return;

        }

        public int countRef()
        {
            int value =  Math.Max(this.row.count(), this.col.count());
            return Math.Max(value, this.box.count());
        }

        public bool checkValid(int value)
        {
            if(!this.row.check(value)||!this.col.check(value)||!this.box.check(value))
            {
                return false;
            }
            return true;
        }

        public bool isSolved()
        {
            if (!this.box.checkValid() || !this.col.checkValid() || !this.row.checkValid())
            {
                return false;
            }
            return true;
                
        }
    }
}
