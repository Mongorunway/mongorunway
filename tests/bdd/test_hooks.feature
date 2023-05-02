# Copyright (c) 2023 Animatea
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Feature: Testing migration hooks

  Scenario: Recalculate migration checksum when a file is modified
    Given we have a configured migration application
    When we create a migration file and obtain a complete migration object for further testing
    When we add the obtained migration to the database, simulating a real use case
    Then we check if their checksums are equal
    When we open the migration file and modify it, thereby changing the checksum of the migration
    Then we obtain the current state of the modified migration file and the unchanged migration from the database
      """
      and assert that their checksums are not equal, as the file has been modified
      """
    When we create a hook that allows resolving this conflict by recalculating all checksums and apply it to the application
    Then we obtain the current state of the migration from the file and the current state of the migration
      """
      in the database and assert that they are equal, as the hook that recalculates their checksums has
      been applied.
      """

  Scenario: Raise if migration file checksum mismatch
    Given we have a configured migration application
    When we create a migration file and obtain a complete migration object for further testing
    When we add the obtained migration to the database, simulating a real use case
    Then we check if their checksums are equal
    Then we apply the hook and it doesn't throw an exception because the migration file hasn't changed
    When we open the migration file and modify it, thereby changing the checksum of the migration
    Then we apply the hook after changing the migration file and get a MigrationFileChangedError exception
      """
      because the migration file has been changed
      """
